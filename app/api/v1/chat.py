from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, File, UploadFile
from starlette.websockets import WebSocketState
from pydantic import BaseModel
from typing import Optional, List
from app.agent.graph import agent_executor
from app.api.deps import get_current_user, get_user_from_token
from app.db.supabase_client import supabase
from datetime import datetime
import json
import asyncio
import io
import os
from pypdf import PdfReader

def log_to_file(message):
    log_path = os.path.join(os.getcwd(), "debug_log.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {message}\n")

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except (WebSocketDisconnect, RuntimeError):
            # Connection already closed, ignore
            pass

manager = ConnectionManager()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        # 1. Get conversation history if conversation_id provided
        conversation_id = request.conversation_id
        history_messages = []
        
        if conversation_id and supabase:
            try:
                # 1a. Verify conversation ownership
                conv_check = supabase.table("conversations")\
                    .select("id")\
                    .eq("id", conversation_id)\
                    .eq("user_id", current_user["id"])\
                    .execute()
                
                if not conv_check.data:
                    # If conversation doesn't belong to user, treat as new or error
                    # Better to raise error to prevent unauthorized history leakage
                    raise HTTPException(status_code=403, detail="Access denied to conversation")

                # Fetch previous messages (up to 20 for context)
                msg_result = supabase.table("messages")\
                    .select("role, content")\
                    .eq("conversation_id", conversation_id)\
                    .order("created_at", desc=False)\
                    .limit(20)\
                    .execute()
                
                for msg in msg_result.data:
                    history_messages.append((msg["role"], msg["content"]))
            except Exception as db_error:
                # Log but continue - database is optional
                print(f"Warning: Could not fetch history: {db_error}")
        
        # 2. Add current user message
        history_messages.append(("user", request.message))
        
        # 3. Call agent with thread_id for memory
        input_state = {"messages": history_messages}
        config = {"configurable": {"thread_id": conversation_id}}
        output_state = await agent_executor.ainvoke(input_state, config=config)
        last_message = output_state["messages"][-1]
        
        # Robustly handle content that might be a string or a list of parts (like with Gemini)
        def _get_text_content(content):
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
            return str(content)
            
        assistant_response = _get_text_content(last_message.content)
        
        # 4. Save messages to database (optional - won't break if fails)
        if supabase:
            try:
                # Create conversation if needed
                if not conversation_id:
                    user_id = current_user["id"]
                    conv_result = supabase.table("conversations").insert({
                        "title": request.message[:50] + "...",
                        "user_id": user_id
                    }).execute()
                    if conv_result.data:
                        conversation_id = conv_result.data[0]["id"]
                
                # Save both messages
                if conversation_id:
                    supabase.table("messages").insert([
                        {
                            "conversation_id": conversation_id,
                            "role": "user",
                            "content": request.message
                        },
                        {
                            "conversation_id": conversation_id,
                            "role": "assistant",
                            "content": assistant_response
                        }
                    ]).execute()
                    
                    # 5. Update conversation timestamp
                    supabase.table("conversations")\
                        .update({"updated_at": datetime.utcnow().isoformat()})\
                        .eq("id", conversation_id)\
                        .execute()
            except Exception as db_error:
                # Database save failed but chat still works. Log the error.
                print(f"CRITICAL: Could not save to database: {db_error}")
                # You might want to log this to a file or monitoring service
        
        log_to_file(f"DEBUG Chat: Sending response to frontend via POST: {assistant_response[:100]}...")
        print(f"DEBUG Chat: Sending response to frontend via POST: {assistant_response[:100]}...")
        return ChatResponse(
            response=assistant_response,
            conversation_id=conversation_id
        )
    except Exception as e:
        # Only raise if it's not a database error
        if "row-level security" in str(e).lower():
            # RLS error - return response without saving
            raise HTTPException(
                status_code=500,
                detail=f"Database RLS error (chat still works): {str(e)[:100]}"
            )

        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/messages/{message_id}")
async def delete_message(message_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a specific message if owned by user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        # 1. Fetch message to find conversation_id
        res = await asyncio.to_thread(
            lambda: supabase.table("messages").select("conversation_id").eq("id", message_id).execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Message not found")
        
        conversation_id = res.data[0]["conversation_id"]
        
        # 2. Verify ownership of the conversation
        conv_res = await asyncio.to_thread(
            lambda: supabase.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
        )
        if not conv_res.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 3. Delete the message
        await asyncio.to_thread(
            lambda: supabase.table("messages").delete().eq("id", message_id).execute()
        )
        
        return {"message": "Message deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/upload/{conversation_id}")
async def upload_pdf(
    conversation_id: str, 
    file: UploadFile = File(...), 
    silent: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Xử lý tệp PDF và đưa vào ngữ cảnh AI. Nếu silent=True, sẽ không lưu tin nhắn xác nhận vào DB."""
    filename = file.filename or "unknown.pdf"
    print(f"\n>>> [SENTINEL] UPLOAD START: {filename} (Conv: {conversation_id})", flush=True)
    
    try:
        user_id = current_user.get("id")
        print(f">>> [SENTINEL] User: {user_id}", flush=True)
        
        # 0. Kiểm tra quyền sở hữu
        print(f">>> [SENTINEL] Step 0: Ownership check", flush=True)
        conv_check = await asyncio.to_thread(
            lambda: supabase.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
        )
        if not conv_check.data:
            print(f">>> [SENTINEL] Ownership failed for {conversation_id}", flush=True)
            raise HTTPException(status_code=403, detail="Không có quyền truy cập đoạn chat này")

        print(f">>> [SENTINEL] Ownership verified for {conversation_id}", flush=True)

        # 1. Read and Parse PDF
        try:
            await file.seek(0)
            content = await file.read()
            pdf = PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
            
            # Clean text of null bytes that can break database inserts
            text = text.replace('\x00', '')
            
            if not text.strip():
                raise ValueError("PDF không chứa văn bản có thể đọc được")
        except Exception as pdf_err:
            raise HTTPException(status_code=400, detail=f"Lỗi đọc PDF: {str(pdf_err)}")
        finally:
            await file.close()

        # 2. Update Agent Memory (State)
        try:
            config = {"configurable": {"thread_id": conversation_id}}
            current_state = await agent_executor.aget_state(config)
            existing_pdf_context = ""
            if current_state and current_state.values:
                existing_pdf_context = current_state.values.get("pdf_context", "")
            
            updated_context = existing_pdf_context + f"\n\n--- DOCUMENT: {file.filename} ---\n{text}"
            await agent_executor.aupdate_state(config, {"pdf_context": updated_context})
            print(f"DEBUG: Agent state updated correctly", flush=True)
        except Exception as state_err:
            print(f"WARNING: Memory Update Failed: {state_err}", flush=True)

        # 3. Lưu tin nhắn vào Database (Chỉ khi không ở chế độ silent)
        system_msg_content = (
            f"[PDF_ATTACHMENT]\n"
            f"Filename: {filename}\n"
            f"Size: {len(text)} chars\n"
            f"---CONTENT---\n"
            f"{text[:2000].strip()}\n"
            f"[/PDF_ATTACHMENT]"
        )
        
        if not silent:
            try:
                await asyncio.to_thread(
                    lambda: supabase.table("messages").insert({
                        "conversation_id": conversation_id,
                        "role": "assistant",
                        "content": system_msg_content
                    }).execute()
                )
                print(f"DEBUG: Message saved to DB", flush=True)
            except Exception as db_err:
                print(f"DEBUG: DB Error: {db_err}", flush=True)
                raise HTTPException(status_code=500, detail=f"Lỗi lưu Database: {str(db_err)}")
        else:
            print(f"DEBUG: Skipping DB Save (Silent Mode)", flush=True)
        
        return {
            "status": "success", 
            "filename": filename, 
            "message": system_msg_content,
            "extracted_text": text
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_msg = str(e)
        full_trace = traceback.format_exc()
        print(f"CRITICAL ERROR in upload_pdf: {err_msg}\n{full_trace}", flush=True)
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {err_msg}\n{full_trace[:200]}")
@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, conversation_id: Optional[str] = None, token: Optional[str] = None):
    # 1. Accept connection IMMEDIATELY to prevent timeouts
    try:
        await websocket.accept()
        manager.active_connections.append(websocket)
        print(f"DEBUG: WS Connection accepted. Client state: {websocket.client_state}. Token present: {bool(token)}, Conv ID: {conversation_id}")
    except Exception as e:
        print(f"CRITICAL: Failed to accept WS connection: {e}")
        return

    # 2. Authenticate user via token
    user = None
    try:
        if token:
            # Check if get_user_from_token is async or sync. Assuming sync based on usage but wrapping just in case
            if asyncio.iscoroutinefunction(get_user_from_token):
                user = await get_user_from_token(token)
            else:
                user = get_user_from_token(token)
    except Exception as auth_err:
        print(f"DEBUG: WS Auth Error: {auth_err}")
    
    if not user:
        print(f"DEBUG: WS Auth FAILED for token: {token[:10] if token else 'None'}...")
        # Connection is already accepted, so we send error and close
        await manager.send_personal_message(json.dumps({"type": "error", "content": "Unauthorized"}), websocket)
        manager.disconnect(websocket)
        await websocket.close()
        return

    user_id = user["id"]
    
    try:
        # Verify conversation ownership if ID exists
        if conversation_id:
            conv_check = await asyncio.to_thread(
                lambda: supabase.table("conversations")\
                    .select("id")\
                    .eq("id", conversation_id)\
                    .eq("user_id", user_id)\
                    .execute()
            )
            if not conv_check.data:
                await manager.send_personal_message(json.dumps({"type": "error", "content": "Access denied to conversation"}), websocket)
                manager.disconnect(websocket)
                await websocket.close()
                return

        while True:
            # Check state before receiving
            if websocket.client_state == WebSocketState.DISCONNECTED:
                 print(f"DEBUG: WS State is DISCONNECTED, breaking loop")
                 break
                 
            data = await websocket.receive_text()
            print(f"DEBUG: WS Received data: {data}")
            
            # Retrieve conversation history for context (up to 20 messages)
            history_messages = []
            if conversation_id and supabase:
                 try:
                    msg_result = await asyncio.to_thread(
                        lambda: supabase.table("messages")\
                            .select("role, content")\
                            .eq("conversation_id", conversation_id)\
                            .order("created_at", desc=False)\
                            .limit(20)\
                            .execute()
                    )
                    for msg in msg_result.data:
                        history_messages.append((msg["role"], msg["content"]))
                 except Exception as history_err: 
                     print(f"Error loading WS history for {conversation_id}: {history_err}")
            
            history_messages.append(("user", data))
            
            if not conversation_id and supabase:
                try:
                    print(f"DEBUG: Creating new conversation for user {user_id}")
                    res = await asyncio.to_thread(
                        lambda: supabase.table("conversations").insert({
                            "title": data[:50], 
                            "user_id": user_id
                        }).execute()
                    )
                    print(f"DEBUG: New conversation insert result: {res.data if res.data else 'EMPTY'}")
                    if res.data:
                        conversation_id = res.data[0]["id"]
                        print(f"DEBUG: New conversation created: {conversation_id}")
                        # Send meta immediately so frontend knows its ID
                        await manager.send_personal_message(json.dumps({
                            "type": "meta",
                            "conversation_id": conversation_id
                        }), websocket)
                    else:
                        print(f"WARNING: Conversation insert returned empty data (Likely RLS issue despite service key?)")
                except Exception as e:
                    print(f"Error creating conversation: {e}")

            if conversation_id and supabase:
                try:
                    await asyncio.to_thread(
                        lambda: supabase.table("messages").insert({
                            "conversation_id": conversation_id,
                            "role": "user",
                            "content": data
                        }).execute()
                    )
                    print(f"DEBUG: User message saved to conversation {conversation_id}")
                except Exception as e:
                    print(f"Error saving user message to conversation {conversation_id}: {e}")

            # 3. Stream Agent Response
            try:
                print(f"DEBUG Chat: Starting agent stream for conversation {conversation_id}")
                import time
                total_start = time.time()
                await manager.send_personal_message(json.dumps({"type": "start"}), websocket)
                full_response = ""
                tokens_streamed = 0  # Track if we actually streamed anything
                
                # Pass thread_id to enable checkpointer/memory
                config = {"configurable": {"thread_id": conversation_id}}
                print(f"DEBUG Chat: Config ID: {conversation_id}")
                
                async for event in agent_executor.astream_events(
                    {"messages": history_messages},
                    config=config,
                    version="v2"
                ):
                    kind = event["event"]
                    # debug log removed to reduce noise
                    if kind == "on_tool_start":
                        print(f"DEBUG: Tool Start: {event['name']} with input: {event['data'].get('input')}")
                        await manager.send_personal_message(json.dumps({
                            "type": "status", 
                            "content": f"Running tool: {event['name']}..."
                        }), websocket)
                    elif kind == "on_tool_end":
                        print(f"DEBUG: Tool End: {event['name']}")
                    elif kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        
                        if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
                            continue
                        
                        if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs.get('tool_calls') and not chunk.content:
                            continue
                            
                        content = chunk.content
                        if isinstance(content, list):
                            content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
                        
                        if content:
                            full_response += content
                            tokens_streamed += 1
                            await manager.send_personal_message(json.dumps({
                                "type": "token", 
                                "content": content
                            }), websocket)
                            
                # FALLBACK: If we didn't stream any tokens but the model generated a response
                if tokens_streamed == 0 and not full_response:
                    print("WARNING: No tokens were streamed, attempting to extract from final state...")
                    try:
                        state_snapshot = await agent_executor.aget_state(config)
                        if state_snapshot and "messages" in state_snapshot.values:
                            messages = state_snapshot.values["messages"]
                            if messages and len(messages) > 0:
                                last_message = messages[-1]
                                if hasattr(last_message, 'content') and last_message.content:
                                    full_response = last_message.content
                                    print(f"FALLBACK: Extracted {len(full_response)} chars from final message")
                                    await manager.send_personal_message(json.dumps({
                                        "type": "token",
                                        "content": full_response
                                    }), websocket)
                    except Exception as fallback_err:
                        print(f"FALLBACK ERROR: {fallback_err}")
                        
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                return
            except Exception as graph_err:
                print(f"Error in agent graph execution: {graph_err}")
                await manager.send_personal_message(json.dumps({
                    "type": "error",
                    "content": f"Lỗi hệ thống AI: {str(graph_err)[:100]}"
                }), websocket)
                continue

            # 4. Send end signal
            latency = time.time() - total_start
            log_to_file(f"DEBUG Chat: WS Response complete. Latency: {latency:.2f}s, Tokens: {tokens_streamed}")
            print(f"DEBUG Chat: WS Response complete. Total Latency: {latency:.2f}s, Tokens streamed: {tokens_streamed}, Response length: {len(full_response)}")
            print(f"DEBUG Chat: Sending final response to WS client: {full_response[:100]}...")
            await manager.send_personal_message(json.dumps({
                "type": "end",
                "full_content": full_response
            }), websocket)
            
            # 5. Save Assistant Message and Update Timestamp
            if conversation_id and supabase:
                try:
                    await asyncio.to_thread(
                        lambda: supabase.table("messages").insert({
                            "conversation_id": conversation_id,
                            "role": "assistant",
                            "content": full_response
                        }).execute()
                    )
                    
                    await asyncio.to_thread(
                        lambda: supabase.table("conversations")\
                            .update({"updated_at": datetime.utcnow().isoformat()})\
                            .eq("id", conversation_id)\
                            .execute()
                    )
                except Exception as e:
                    print(f"Error saving assistant message for conversation {conversation_id}: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("DEBUG: Client disconnected gracefully")
    except Exception as e:
        print(f"CRITICAL WS ERROR: {e}")
        manager.disconnect(websocket)

