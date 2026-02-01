"""
LegalBot AI - Unified Tools System
===================================
Contains 5 specialized tools for comprehensive legal assistance:
1. legal_assistant - Main knowledge base + vector search
2. web_search - Real-time internet search
3. calculate_fee - Fee calculator
4. get_date_info - Date and deadline helper
5. format_document - Document checklist formatter
"""

from langchain_core.tools import tool
from app.core.resources import resources
from datetime import datetime, timedelta
from typing import Optional
import time

# ============================================================================
# TOOL 1: Legal Assistant (Primary Knowledge + Vector Search)
# ============================================================================

@tool
async def legal_assistant(query: str) -> str:
    """
    Trả lời câu hỏi về pháp luật và thủ tục hành chính Việt Nam.
    Sử dụng kiến thức có sẵn kết hợp tìm kiếm vector database.
    
    Args:
        query: Câu hỏi của người dùng
        
    Returns:
        Câu trả lời chi tiết về thủ tục hoặc pháp luật
    """
    start_time = time.time()
    
    try:
        # Normalize query
        query_lower = query.lower().strip()
        
        # Knowledge Base - Common procedures
        procedures = {
            "giấy phép lái xe": {
                "title": "Thủ tục Cấp/Đổi Giấy Phép Lái Xe",
                "steps": [
                    "1. Khám sức khỏe lái xe tại cơ sở y tế có thẩm quyền",
                    "2. Nộp hồ sơ trực tuyến qua https://dichvucong.gov.vn hoặc trực tiếp tại Sở GTVT",
                    "3. Chụp ảnh và đóng lệ phí",
                    "4. Nhận giấy hẹn",
                    "5. Nhận GPLX (trực tiếp hoặc qua bưu điện)"
                ],
                "documents": [
                    "Đơn đề nghị (mẫu có sẵn)",
                    "Giấy khám sức khỏe lái xe",
                    "GPLX cũ (nếu đổi)",
                    "CCCD gốc",
                    "Ảnh 3x4 (chụp tại nơi làm)"
                ],
                "time": "5-10 ngày làm việc",
                "fee": "135,000 VNĐ + phí khám (~300k)",
                "note": "Có thể làm online 100% nếu có VNeID"
            },
            "đăng ký kết hôn": {
                "title": "Thủ tục Đăng Ký Kết Hôn",
                "steps": [
                    "1. Chuẩn bị hồ sơ đầy đủ",
                    "2. Nộp hồ sơ tại UBND phường/xã nơi một trong hai bên cư trú",
                    "3. Chờ thẩm tra (3 ngày làm việc)",
                    "4. Đến đăng ký và ký tên",
                    "5. Nhận Giấy chứng nhận kết hôn"
                ],
                "documents": [
                    "Đơn đăng ký kết hôn",
                    "CMND/CCCD cả hai bên",
                    "Giấy xác nhận tình trạng hôn nhân",
                    "Sổ hộ khẩu"
                ],
                "time": "3 ngày làm việc",
                "fee": "0 VNĐ (miễn phí)",
                "note": "Cả hai bên phải có mặt khi đăng ký"
            },
            "đăng ký kinh doanh": {
                "title": "Thủ tục Đăng Ký Kinh Doanh",
                "steps": [
                    "1. Đăng ký tài khoản tại https://dangkykinhdoanh.gov.vn",
                    "2. Điền thông tin doanh nghiệp",
                    "3. Upload hồ sơ (CMND, địa chỉ, điều lệ)",
                    "4. Nộp phí online",
                    "5. Nhận Giấy CNĐKDN qua email hoặc bưu điện"
                ],
                "documents": [
                    "CMND/CCCD người đại diện",
                    "Địa chỉ trụ sở (hợp đồng thuê/sở hữu)",
                    "Điều lệ công ty (nếu là công ty)"
                ],
                "time": "3-5 ngày",
                "fee": "Hộ KD: 40-100k, Công ty: 300-500k",
                "note": "100% online, không cần đến trực tiếp"
            },
            "ly hôn": {
                "title": "Thủ tục Ly Hôn",
                "steps": [
                    "1. Gửi đơn tại TAND cấp huyện nơi bị đơn cư trú/làm việc",
                    "2. Thụ lý đơn và nộp tạm ứng án phí",
                    "3. Tham gia phiên họp kiểm tra việc giao nộp, tiếp cận vật chứng",
                    "4. Hòa giải sơ thẩm (nếu không được sẽ đưa ra xét xử)",
                    "5. Tòa ra Bản án hoặc Quyết định ly hôn"
                ],
                "documents": [
                    "Đơn xin ly hôn",
                    "Giấy chứng nhận đăng ký kết hôn (Bản chính)",
                    "CCCD của vợ/chồng (Bản sao công chứng)",
                    "Giấy khai sinh của các con",
                    "Giấy tờ về tài sản chung (Sổ đỏ, đăng ký xe...)"
                ],
                "time": "3-6 tháng",
                "fee": "300,000 VNĐ án phí sơ thẩm",
                "note": "Ly hôn thuận tình sẽ nhanh hơn ly hôn đơn phương",
                "suggestions": ["Quyền nuôi con sau khi ly hôn", "Cách phân chia tài sản chung", "Giá thuê luật sư ly hôn 2024"]
            },
            "thông báo mẫu dấu": {
                "title": "Thủ tục Thông báo Mẫu con dấu",
                "steps": [
                    "1. Doanh nghiệp tự khắc dấu",
                    "2. Thông báo mẫu dấu qua mạng tại Cổng thông tin quốc gia",
                    "3. Hệ thống tiếp nhận và cấp Giấy xác nhận"
                ],
                "documents": [
                    "Thông báo theo mẫu của Bộ Kế hoạch và Đầu tư"
                ],
                "time": "1-3 ngày",
                "fee": "Miễn phí",
                "note": "Từ 2021 doanh nghiệp không bắt buộc phải thông báo mẫu dấu lên cổng thông tin"
            },
            "tạm ngừng kinh doanh": {
                "title": "Thủ tục Tạm ngừng Kinh Doanh",
                "steps": [
                    "1. Thông báo cho cơ quan ĐKKD ít nhất 3 ngày làm việc trước khi tạm ngừng",
                    "2. Nộp hồ sơ qua mạng tại Cổng thông tin quốc gia",
                    "3. Nhận Giấy xác nhận tạm ngừng"
                ],
                "documents": [
                    "Thông báo tạm ngừng",
                    "Nghị quyết/Quyết định của chủ sở hữu/HĐTV/HĐQT"
                ],
                "time": "3 ngày làm việc",
                "fee": "Miễn phí",
                "note": "Tổng thời gian tạm ngừng không quá 02 năm liên tiếp",
                "suggestions": ["Thủ tục đóng mã số thuế doanh nghiệp", "Cách tính thuế khi tạm ngừng kinh doanh", "Điều kiện để doanh nghiệp hoạt động trở lại trước thời hạn"]
            },
            "thành lập doanh nghiệp": {
                "title": "Thủ tục Thành lập Công ty TNHH/Cổ phần",
                "steps": [
                    "1. Chuẩn bị thông tin (tên, địa chỉ, vốn, ngành nghề)",
                    "2. Soạn hồ sơ đăng ký doanh nghiệp trực tuyến",
                    "3. Nộp hồ sơ tại Cổng thông tin quốc gia về đăng ký doanh nghiệp",
                    "4. Nhận kết quả và Giấy chứng nhận ĐKDN",
                    "5. Khắc dấu và công bố thông tin doanh nghiệp"
                ],
                "documents": [
                    "Giấy đề nghị đăng ký doanh nghiệp",
                    "Điều lệ công ty",
                    "Danh sách thành viên/cổ đông sáng lập",
                    "Bản sao CCCD/Hộ chiếu các thành viên"
                ],
                "time": "3-5 ngày làm việc",
                "fee": "Lệ phí ĐK: 50k, Phí công bố: 300k",
                "note": "Nên đăng ký tài khoản kinh doanh trước tại dangkykinhdoanh.gov.vn",
                "suggestions": ["Sự khác biệt giữa Công ty TNHH và Cổ phần", "Cách đặt tên công ty không bị trùng", "Thủ tục sau khi nhận giấy phép kinh doanh"]
            },
            "thừa kế": {
                "title": "Thủ tục Khai nhận Di sản Thừa kế",
                "steps": [
                    "1. Chuẩn bị hồ sơ chứng minh quan hệ và tài sản",
                    "2. Đến văn phòng Công chứng để lập văn bản khai nhận",
                    "3. Niêm yết thông báo thừa kế tại UBND xã/phường (15 ngày)",
                    "4. Ký văn bản khai nhận/phân chia di sản",
                    "5. Đăng ký sang tên tài sản (nếu là nhà đất/xe)"
                ],
                "documents": [
                    "Giấy chứng tử của người để lại di sản",
                    "Di chúc (nếu có)",
                    "Giấy tờ chứng minh quan hệ (Khai sinh, kết hôn, hộ khẩu)",
                    "Giấy chứng nhận quyền sử dụng đất/đăng ký xe"
                ],
                "time": "20-30 ngày",
                "fee": "Phí công chứng + Thuế thu nhập (nếu không được miễn)",
                "note": "Miễn thuế nếu thừa kế giữa cha mẹ - con cái, anh chị em ruột",
                "suggestions": ["Thủ tục khai nhận di sản thừa kế tại văn phòng công chứng", "Thuế thu nhập cá nhân khi bán nhà đất thừa kế", "Chia thừa kế theo pháp luật khi không có di chúc"]
            },
            "sổ đỏ": {
                "title": "Thủ tục Cấp/Sang tên Sổ đỏ (Giấy chứng nhận Quyền sử dụng đất)",
                "steps": [
                    "1. Nộp hồ sơ tại Văn phòng đăng ký đất đai hoặc UBND cấp huyện",
                    "2. Cơ quan chức năng kiểm tra hồ sơ và hiện trạng",
                    "3. Thực hiện nghĩa vụ tài chính (thuế, phí)",
                    "4. Nhận Giấy chứng nhận mới hoặc xác nhận sang tên"
                ],
                "documents": [
                    "Đơn đăng ký biến động đất đai",
                    "Giấy chứng nhận quyền sử dụng đất (Bản gốc)",
                    "Hợp đồng chuyển nhượng/tặng cho (Công chứng)",
                    "Tờ khai thuế thu nhập cá nhân và lệ phí trước bạ"
                ],
                "time": "15-30 ngày làm việc",
                "fee": "Lệ phí trước bạ (0.5%), Thuế TNCN (2%)",
                "note": "Kiểm tra kỹ thông tin quy hoạch trước khi giao dịch",
                "suggestions": ["Thủ tục xóa nợ thuế đất để sang tên sổ đỏ", "Chi phí làm sổ đỏ lần đầu", "Hợp đồng đặt cọc mua bán đất chuẩn pháp lý"]
            },
            "tạm trú": {
                "title": "Thủ tục Đăng ký Tạm trú",
                "steps": [
                    "1. Chuẩn bị hồ sơ pháp lý về chỗ ở",
                    "2. Nộp hồ sơ tại Công an xã/phường hoặc qua Cổng dịch vụ công Bộ Công an",
                    "3. Cán bộ tiếp nhận và kiểm tra thông tin",
                    "4. Nhận thông báo kết quả đăng ký cư trú"
                ],
                "documents": [
                    "Tờ khai thay đổi thông tin cư trú (mẫu CT01)",
                    "Hợp đồng thuê nhà hoặc giấy tờ chứng minh chỗ ở hợp pháp",
                    "CCCD/Hộ chiếu của người đăng ký"
                ],
                "time": "3 ngày làm việc",
                "fee": "15,000 VNĐ (nộp trực tiếp), 7,000 VNĐ (trực tuyến)",
                "note": "Đăng ký qua dịch vụ công trực tuyến sẽ nhanh và rẻ hơn",
                "suggestions": ["Đăng ký tạm trú qua VNeID như thế nào?", "Xác nhận thông tin cư trú (CT07) xin ở đâu?", "Mức phạt khi không đăng ký tạm trú"]
            }
        }
        
        # Check knowledge base first (instant response)
        matched_key = None
        # Better matching: use keyword groups for each procedure
        key_map = {
            "giấy phép lái xe": ["giấy phép lái xe", "bằng lái", "gplx"],
            "đăng ký kết hôn": ["kết hôn", "lấy vợ", "lấy chồng"],
            "đăng ký kinh doanh": ["đăng ký kinh doanh", "hộ kinh doanh"],
            "ly hôn": ["ly hôn", "chia tay"],
            "thành lập doanh nghiệp": ["thành lập doanh nghiệp", "thành lập công ty", "mở công ty"],
            "thừa kế": ["thừa kế", "di sản"],
            "sổ đỏ": ["sổ đỏ", "sổ hồng", "quyền sử dụng đất", "đất đai"],
            "tạm trú": ["tạm trú", "vắng mặt"],
            "thông báo mẫu dấu": ["mẫu dấu", "con dấu"],
            "tạm ngừng kinh doanh": ["tạm ngừng kinh doanh", "ngừng kinh doanh"],
            "giao thông": ["giao thông", "xe máy", "ô tô", "biển báo", "bị phạt"]
        }
        
        for key, keywords in key_map.items():
            if any(kw in query_lower for kw in keywords):
                matched_key = key
                break
        
        if matched_key:
            if matched_key == "giao thông":
                return """## Tra cứu Luật Giao thông Đường bộ
                
Tôi đã tìm thấy tài liệu về **Trật tự, an toàn giao thông đường bộ**. Bạn có thể hỏi cụ thể về:
- Các quy tắc tham gia giao thông (đi bộ, xe máy, ô tô).
- Điều kiện phương tiện và người điều khiển.
- Các hành vi bị nghiêm cấm và mức xử phạt.
- Hệ thống biển báo và tín hiệu đèn.

*Gợi ý: Hãy đặt câu hỏi cụ thể như "Mức phạt nồng độ cồn" hoặc "Quy tắc vượt xe" để tôi tra cứu chi tiết nhé!*"""
            
            proc = procedures[matched_key]
            print(f"DEBUG legal_assistant: KB Match found for '{matched_key}'")
            response = f"## {proc['title']}\n\n### CÁC BƯỚC THỰC HIỆN:\n"
            response += chr(10).join(proc['steps'])
            response += "\n\n### HỒ SƠ CẦN THIẾT:\n"
            response += chr(10).join([f'- {doc}' for doc in proc['documents']])
            response += f"\n\n### THỜI GIAN: {proc['time']}\n### PHÍ: {proc['fee']}\n### LƯU Ý: {proc['note']}\n"
            
            print(f"DEBUG legal_assistant: Knowledge base match in {time.time() - start_time:.2f}s")
            return response
        
        # If no match in knowledge base, try vector search (with timeout)
        print("DEBUG legal_assistant: No KB match, optimizing query for vector search...")
        
        search_query = query # Fallback if optimizer fails
        try:
            fast_llm = resources.fast_llm
            if fast_llm:
                print("DEBUG: Calling Optimizer (LLM)...")
                opt_prompt = f"""Bạn là chuyên gia tra cứu pháp luật Việt Nam. 
Nhiệm vụ: Chuyển đổi câu hỏi của người dùng (có thể có lỗi chính tả) thành một chuỗi từ khóa (keywords) ngắn gọn, súc tích để tìm kiếm trong cơ sở dữ liệu luật.

QUY TẮC:
- Trích xuất 3-5 từ khóa quan trọng nhất.
- Sửa lỗi chính tả nếu có (VD: "quy tậc" -> "quy tắc").
- Ngôn ngữ: Tiếng Việt.
- CHỈ TRẢ VỀ TỪ KHÓA, không thêm bất kỳ lời dẫn nào.

Câu hỏi: {query}
Từ khóa tìm kiếm:"""
                # Add 5 second timeout for optimization
                import asyncio
                try:
                    opt_res = await asyncio.wait_for(fast_llm.ainvoke(opt_prompt), timeout=5.0)
                    search_query = opt_res.content.strip()
                    print(f"DEBUG legal_assistant: Optimized query: '{search_query}'")
                except asyncio.TimeoutError:
                    print("DEBUG legal_assistant: Optimizer timed out, using original query.")
        except Exception as opt_err:
            print(f"DEBUG legal_assistant: Query optimization failed (using original): {opt_err}")

        try:
            print("DEBUG: Preparing Vector Search (Check Resources)...")
            embeddings = resources.embeddings
            index = resources.get_index()
            
            if not index:
                return "⚠️ Xin lỗi, hệ thống tra cứu đang tạm thời không khả dụng. Vui lòng thử lại sau."
            
            print(f"DEBUG: Generating Vector for '{search_query}'...")
            # Embed the optimized query
            query_vector = embeddings.embed_query(search_query)
            print("DEBUG: Vector generated. Querying Pinecone...")
            
            # Search Pinecone (Target the "Corpus" namespace where PDF data is stored)
            results = index.query(
                vector=query_vector,
                top_k=3,
                include_metadata=True,
                namespace="Corpus"
            )
            
            if not results or not results.get('matches'):
                return f"""[FALLBACK_SIGNAL] Tôi chưa tìm thấy thông tin chi tiết về "{query}" trong cơ sở dữ liệu luật nội bộ.
                
Bạn vui lòng sử dụng công cụ `web_search` để tìm kiếm thông tin mới nhất trên internet hoặc hỏi về các dịch vụ phổ biến: GPLX, Kết hôn, Ly hôn, ĐK Kinh doanh."""
            
            # Format vector search results
            formatted_results = []
            for i, match in enumerate(results['matches'][:3], 1):
                metadata = match.get('metadata', {})
                text = metadata.get('text', '')[:800]  # Limit to 800 chars
                source = metadata.get('source', 'Không rõ nguồn')
                score = match.get('score', 0)
                
                formatted_results.append(f"""### Kết quả {i} (Độ liên quan: {score:.0%})
**Nguồn:** {source}
**Nội dung:** {text}...""")
            
            result_text = "\n\n".join(formatted_results)
            print(f"DEBUG legal_assistant: Vector search completed in {time.time() - start_time:.2f}s")
            
            return f"""Dựa trên tài liệu pháp luật, tôi tìm thấy thông tin sau:

{result_text}

💡 **Lưu ý:** Đây là tham khảo chung. Nên liên hệ cơ quan có thẩm quyền để biết chính xác."""
            
        except Exception as vector_error:
            print(f"ERROR legal_assistant vector search: {vector_error}")
            return f"""[FALLBACK_SIGNAL] Hệ thống tra cứu nội bộ đang gặp sự cố. Vui lòng sử dụng công cụ `web_search` để tìm kiếm từ internet hoặc diễn đạt lại câu hỏi."""
            
    except Exception as e:
        print(f"ERROR legal_assistant: {e}")
        return f"⚠️ Xin lỗi, đã có lỗi khi xử lý câu hỏi. Vui lòng thử lại."


# ============================================================================
# TOOL 2: Web Search (DuckDuckGo)
# ============================================================================

@tool
def web_search(query: str) -> str:
    """
    Tìm kiếm thông tin pháp luật mới nhất trên internet.
    Hữu ích cho tin tức, luật mới, án lệ gần đây.
    
    Args:
        query: Nội dung cần tìm kiếm
        
    Returns:
        Tóm tắt kết quả tìm kiếm với link nguồn
    """
    try:
        from duckduckgo_search import DDGS
        
        print(f"DEBUG web_search: Searching for '{query}'")
        
        # Search with DuckDuckGo
        ddgs = DDGS()
        # Relaxed search to get more results
        results = ddgs.text(
            f"{query} pháp luật việt nam",
            region='vn-vi',
            max_results=5
        )
        
        if not results:
            return f"""Không tìm thấy kết quả web cho "{query}".

**Gợi ý:**
- Thử từ khóa khác
- Sử dụng công cụ tra cứu nội bộ
- Hỏi trực tiếp về thủ tục"""
        
        # Format results
        formatted = []
        for i, r in enumerate(results[:3], 1):
            formatted.append(f"""**{i}. {r['title']}**
{r['body'][:200]}...
🔗 {r['href']}
""")
        
        return f"""### Kết quả tìm kiếm: "{query}"

{chr(10).join(formatted)}

📌 **Lưu ý:** Đây là thông tin từ internet, nên kiểm tra nguồn chính thức."""
        
    except ImportError:
        return "⚠️ Chức năng tìm kiếm web chưa được cài đặt. Vui lòng cài package 'duckduckgo-search'."
    except Exception as e:
        print(f"ERROR web_search: {e}")
        return f"⚠️ Không thể tìm kiếm web lúc này. Lỗi: {str(e)[:100]}"


# ============================================================================
# TOOL 3: Calculate Fee
# ============================================================================

@tool
def calculate_fee(service: str, details: str = "") -> str:
    """
    Tính lệ phí cho các dịch vụ pháp lý, hành chính.
    
    Args:
        service: Loại dịch vụ (đăng ký kinh doanh, ly hôn, công chứng...)
        details: Chi tiết bổ sung (loại hình doanh nghiệp, giá trị tài sản...)
        
    Returns:
        Bảng phí chi tiết
    """
    service_lower = service.lower()
    
    fee_table = {
        "đăng ký kinh doanh": {
            "Hộ kinh doanh": "50,000 VNĐ",
            "Công ty TNHH": "300,000 VNĐ",
            "Công ty cổ phần": "500,000 VNĐ",
            "Doanh nghiệp tư nhân": "100,000 VNĐ"
        },
        "ly hôn": {
            "Ly hôn thuận tình (UBND)": "0 VNĐ (miễn phí)",
            "Ly hôn có tranh chấp (Tòa án)": "200,000 - 500,000 VNĐ",
            "Phí luật sư (nếu thuê)": "5,000,000 - 20,000,000 VNĐ"
        },
        "công chứng": {
            "Hợp đồng mua bán đất (< 100m²)": "500,000 VNĐ",
            "Hợp đồng mua bán đất (100-300m²)": "1,000,000 VNĐ",
            "Hợp đồng vay tiền": "0.5% giá trị (tối thiểu 50k)",
            "Di chúc": "50,000 - 200,000 VNĐ"
        },
        "giấy phép lái xe": {
            "Cấp mới/Đổi GPLX": "135,000 VNĐ",
            "Khám sức khỏe": "~300,000 VNĐ"
        },
        "hộ chiếu": {
            "Hộ chiếu thường (cấp tại địa phương)": "200,000 VNĐ",
            "Cấp lại do bị mất/hư hỏng": "400,000 VNĐ",
            "Gia hạn hộ chiếu": "100,000 VNĐ"
        },
        "visa": {
            "E-visa 30 ngày (nhập cảnh 1 lần)": "25 USD",
            "Visa 90 ngày (nhập cảnh nhiều lần)": "50 USD",
            "Thẻ tạm trú (1-3 năm)": "145 - 155 USD"
        }
    }
    
    # Find matching service
    matched = None
    for key in fee_table:
        if key in service_lower:
            matched = key
            break
    
    if matched:
        fees = fee_table[matched]
        result = f"""### Lệ phí: {matched.upper()}

"""
        for item, fee in fees.items():
            result += f"- **{item}:** {fee}\n"
        
        result += "\n📌 **Lưu ý:** Phí có thể thay đổi, nên kiểm tra với cơ quan trực tiếp."
        return result
    else:
        return f"""Chưa có thông tin lệ phí cho "{service}".

**Các dịch vụ có thể tra:**
- Đăng ký kinh doanh
- Ly hôn
- Công chứng
- Giấy phép lái xe
- Hộ chiếu

Vui lòng chọn một trong các dịch vụ trên."""


# ============================================================================
# TOOL 4: Get Date Info
# ============================================================================

@tool
def get_date_info(query: str = "today") -> str:
    """
    Lấy thông tin ngày tháng, tính deadline, đếm ngày làm việc.
    
    Args:
        query: Yêu cầu (today, deadline 30 days, count workdays...)
        
    Returns:
        Thông tin ngày tháng hoặc kết quả tính toán
    """
    today = datetime.now()
    query_lower = query.lower()
    
    # Simple queries
    if "hôm nay" in query_lower or "today" in query_lower:
        return f"""📅 **Hôm nay:**
- Ngày: {today.strftime('%d/%m/%Y')}
- Thứ: {['Hai', 'Ba', 'Tư', 'Năm', 'Sáu', 'Bảy', 'CN'][today.weekday()]}
- Tuần: {today.isocalendar()[1]}
"""
    
    # Deadline calculation
    if "deadline" in query_lower or "hạn" in query_lower:
        days = 30  # default
        if "15" in query:
            days = 15
        elif "30" in query:
            days = 30
        elif "60" in query:
            days = 60
        elif "90" in query:
            days = 90
        elif "thụ lý" in query_lower:
            days = 8 # Tòa án thụ lý đơn trong 8 ngày (3 ngày phân công, 5 ngày xem xét)
            return f"""⚖️ **Thời hạn thụ lý đơn khởi kiện (Bộ luật TTDS 2015):**
- Theo quy định, trong vòng 03 ngày làm việc kể từ ngày nhận đơn, Chánh án phân công Thẩm phán xem xét.
- Trong vòng 05 ngày làm việc kể từ ngày được phân công, Thẩm phán phải ra quyết định thụ lý/trả đơn/sửa đổi.
-> **Tổng cộng:** Khoảng 08 ngày làm việc."""
            
        deadline = today + timedelta(days=days)
        return f"""⏰ **Tính deadline:**
- Từ ngày: {today.strftime('%d/%m/%Y')}
- Cộng thêm: {days} ngày
- Đến hạn: {deadline.strftime('%d/%m/%Y')} (Thứ {['Hai', 'Ba', 'Tư', 'Năm', 'Sáu', 'Bảy', 'CN'][deadline.weekday()]})

💡 Lưu ý: Đây là tính theo ngày dương lịch, chưa trừ ngày lễ."""
    
    # Default
    return f"""📅 Hôm nay là {today.strftime('%d/%m/%Y')}

**Tôi có thể:**
- Cho biết ngày hôm nay
- Tính deadline (ví dụ: "deadline 30 ngày")
- Đếm ngày làm việc

Bạn cần thông tin gì?"""


# ============================================================================
# TOOL 5: Format Document Checklist
# ============================================================================

@tool
def format_document(document_type: str) -> str:
    """
    Liệt kê hồ sơ cần thiết cho thủ tục hành chính.
    
    Args:
        document_type: Loại thủ tục (kết hôn, kinh doanh, ly hôn...)
        
    Returns:
        Checklist hồ sơ định dạng sẵn
    """
    doc_type_lower = document_type.lower()
    
    checklists = {
        "kết hôn": {
            "title": "Hồ Sơ Đăng Ký Kết Hôn",
            "items": [
                "☐ Đơn đăng ký kết hôn (mẫu có sẵn)",
                "☐ CMND/CCCD (bản chính cả 2 bên)",
                "☐ Sổ hộ khẩu",
                "☐ Giấy xác nhận tình trạng hôn nhân",
                "☐ Giấy khám sức khỏe (nếu yêu cầu)"
            ]
        },
        "ly hôn": {
            "title": "Hồ Sơ Ly Hôn",
            "items": [
                "☐ Đơn ly hôn",
                "☐ CMND/CCCD (bản chính)",
                "☐ Giấy chứng nhận kết hôn",
                "☐ Sổ hộ khẩu",
                "☐ Thỏa thuận về con (nếu có)",
                "☐ Thỏa thuận chia tài sản (nếu có)"
            ]
        },
        "kinh doanh": {
            "title": "Hồ Sơ Đăng Ký Kinh Doanh",
            "items": [
                "☐ CMND/CCCD người đại diện",
                "☐ Địa chỉ trụ sở (hợp đồng thuê/sở hữu)",
                "☐ Điều lệ công ty (nếu CT TNHH, CP)",
                "☐ Danh sách thành viên/cổ đông",
                "☐ Giấy ủy quyền (nếu ủy quyền)"
            ]
        },
        "lái xe": {
            "title": "Hồ Sơ Đổi/Cấp GPLX",
            "items": [
                "☐ Đơn đề nghị (mẫu có sẵn)",
                "☐ Giấy khám sức khỏe lái xe",
                "☐ CCCD (bản chính)",
                "☐ GPLX cũ (nếu đổi)",
                "☐ Ảnh 3x4 (hoặc chụp tại chỗ)"
            ]
        }
    }
    
    # Find match
    matched = None
    # Key mapping for document checklists
    key_map = {
        "kết hôn": ["kết hôn", "lấy vợ", "lấy chồng", "phường"],
        "ly hôn": ["ly hôn", "chia tay", "tòa án"],
        "kinh doanh": ["kinh doanh", "công ty", "doanh nghiệp"],
        "lái xe": ["lái xe", "gplx", "bằng lái"]
    }
    
    for key, keywords in key_map.items():
        if any(kw in doc_type_lower for kw in keywords):
            matched = key
            break
    
    if matched:
        checklist = checklists[matched]
        result = f"""## {checklist['title']}

### CHECKLIST HỒ SƠ:
{chr(10).join(checklist['items'])}

📋 **Cách sử dụng:**
- Đánh dấu ✓ vào ☐ khi chuẩn bị xong
- Mang bản chính để đối chiếu
- Nộp bản photo công chứng (nếu yêu cầu)
"""
        return result
    else:
        return f"""Chưa có checklist cho "{document_type}".

**Checklist có sẵn:**
- Kết hôn
- Ly hôn
- Kinh doanh
- Lái xe (GPLX)

Vui lòng chọn một trong các thủ tục trên."""
