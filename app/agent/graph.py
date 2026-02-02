from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import AgentState
from datetime import datetime
from dotenv import load_dotenv

# Import tools
from app.agent.legal_tools import (
    legal_assistant,
    web_search,
    calculate_fee,
    get_date_info,
    format_document
)

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", "..", ".env")
load_dotenv(env_path)

def log_to_file(message):
    try:
        with open(os.path.join(os.path.dirname(env_path), "debug_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except:
        pass

# 1. Initialize Base Models
# Tier 1: Llama 3.3 70B (High Intelligence)
base_llama_70b = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    streaming=True,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Tier 2: Llama 3.1 8B (High Speed & Reliability)
base_llama_8b = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    streaming=True,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Tier 3: Gemini (Configurable - Fallback Stability)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
base_gemini = None
if os.getenv("GOOGLE_API_KEY"):
    try:
        base_gemini = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        log_to_file(f"INFO: Initialized Gemini model: {GEMINI_MODEL}")
    except Exception as e:
        log_to_file(f"WARNING: Failed to initialize Gemini model '{GEMINI_MODEL}': {e}")
        base_gemini = None
else:
    log_to_file("INFO: GOOGLE_API_KEY not set - skipping Gemini initialization")

# 2. Export global llm for simple tasks (Required by app/services/generator.py)
fallbacks = [base_llama_8b]
if base_gemini is not None:
    fallbacks.append(base_gemini)

llm = base_llama_70b.with_fallbacks(
    fallbacks=fallbacks,
    exceptions_to_handle=(Exception,)
)

# Define Tools
tools = [
    legal_assistant,
    web_search,
    calculate_fee,
    get_date_info,
    format_document
]
tool_node = ToolNode(tools)

# 3. Tool-bound versions for the Agent Graph
llama_70b_with_tools = base_llama_70b.bind_tools(tools)
llama_8b_with_tools = base_llama_8b.bind_tools(tools)
if base_gemini is not None:
    gemini_with_tools = base_gemini.bind_tools(tools)
else:
    gemini_with_tools = None

# Models to try (main -> fallback). Gemini appended only if available
    

async def call_model(state: AgentState):
    summary = state.get("summary", "")
    pdf_context = state.get("pdf_context", "")
    messages = state.get("messages", [])
    
    base_prompt = f"""Bạn là Luật sư Trợ lý AI cao cấp của Việt Nam. 
Nhiệm vụ: Cung cấp tư vấn pháp lý chuyên sâu, chi tiết và có căn cứ.

{"NHẬN DIỆN TÀI LIỆU PDF: " + pdf_context if pdf_context else ""}

QUY TẮC PHẢN HỒI (BẮT BUỘC):
1. ƯU TIÊN CÔNG CỤ: Luôn sử dụng công cụ `legal_assistant` ĐẦU TIÊN cho mọi câu hỏi về pháp luật. 
2. CHẾ ĐỘ FALLBACK: Nếu `legal_assistant` trả về thông báo có thẻ `[FALLBACK_SIGNAL]`, bạn PHẢI ngay lập tức sử dụng công cụ `web_search` để tìm kiếm thông tin thay thế từ internet mà không cần hỏi lại người dùng.
3. HẠN CHẾ WEB SEARCH: Chỉ sử dụng `web_search` khi công cụ nội bộ không có dữ liệu hoặc khi người dùng hỏi về tin tức/sự kiện mới nhất.
4. ƯU TIÊN NỘI DUNG: Luôn trình bày phần phân tích pháp lý và giải thích chi tiết TRƯỚC.
4. CẤU TRÚC: Sử dụng Markdown (H2, H3, Bold, Lists).
5. GỢI Ý (BẮT BUỘC): Kết thúc bằng 3-4 câu hỏi gợi ý trong thẻ [SUGGESTIONS]...[/SUGGESTIONS].
"""
    if summary:
        base_prompt += f"\n\nBẢN TÓM TẮT BỐI CẢNH:\n{summary}"

    formatted_messages = [SystemMessage(content=base_prompt)] + messages
    
    # MANUAL FALLBACK LOOP for maximum reliability in the graph
    models_to_try = [
        ("Llama 3.3 70B", llama_70b_with_tools),
        ("Llama 3.1 8B", llama_8b_with_tools),
        ("Gemini 2.5 Flash", gemini_with_tools)
    ]
    
    last_error = None
    for model_name, model in models_to_try:
        try:
            log_to_file(f"DEBUG Graph: Attempting model {model_name}...")
            response = await model.ainvoke(formatted_messages)
            log_to_file(f"DEBUG Graph: {model_name} SUCCESS.")
            return {"messages": [response]}
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Specific handling for NotFound model errors
            if "not found" in error_str or "models/" in error_str:
                log_to_file(f"WARNING Graph: Model {model_name} returned NotFound error ({error_str[:120]}). Skipping to next fallback.")
                continue

            log_to_file(f"DEBUG Graph: {model_name} FAILED: {error_str[:100]}")
            # If rate limit or similar, continue to fallback
            if "429" in error_str or "rate limit" in error_str or "overloaded" in error_str or "unavailable" in error_str:
                continue
            else:
                # For other errors, also try fallback just in case
                continue

    # All models failed
    from langchain_core.messages import AIMessage
    log_to_file(f"CRITICAL ERROR Graph: All models failed. Last error: {str(last_error)}")
    return {"messages": [AIMessage(content="⚠️ Hệ thống AI hiện đang chịu tải cao. Vui lòng thử lại sau giây lát hoặc làm mới trang.")]}

def should_continue(state: AgentState):
    messages = state["messages"]
    if not messages: return END
    last_message = messages[-1]
    
    tool_calls = [m for m in messages if hasattr(m, 'tool_calls') and m.tool_calls]
    if len(tool_calls) > 4:
        return END

    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.set_entry_point("agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

memory = MemorySaver()
agent_executor = builder.compile(checkpointer=memory)
