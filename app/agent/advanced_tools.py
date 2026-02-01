"""
Advanced tools for LegalBot AI Agent
Implements Case Analyzer, Document Generator, and Procedure Guide
"""
from langchain_core.tools import tool
from typing import Dict, Any
import json

@tool
def analyze_legal_case(situation: str) -> str:
    """
    Phân tích một tình huống pháp lý cụ thể của người dùng.
    CHỈ DÙNG khi người dùng mô tả một vụ việc, tranh chấp hoặc tình huống cần đánh giá rủi ro/quyền lợi.
    KHÔNG DÙNG cho chào hỏi hoặc yêu cầu thay đổi cách xưng hô.
    
    Args:
        situation: Mô tả chi tiết tình huống pháp lý của người dùng
        
    Returns:
        Phân tích có cấu trúc với các vấn đề, quyền lợi và khuyến nghị
    """
    # This is a structured analysis framework
    # The actual legal analysis will be done by the LLM
    # This tool helps structure the output
    
    analysis_template = f"""
PHÂN TÍCH TÌNH HUỐNG:
{situation}

HƯỚNG DẪN PHÂN TÍCH:
1. XÁC ĐỊNH VẤN ĐỀ PHÁP LÝ:
   - Tình huống này liên quan đến lĩnh vực luật nào?
   - Các bên liên quan là ai?
   
2. QUYỀN LỢI CỦA BẠN:
   - Bạn có những quyền gì theo pháp luật?
   - Thời hiệu yêu cầu bảo vệ quyền là bao lâu?
   
3. NGHĨA VỤ VÀ RỦI RO:
   - Bạn có nghĩa vụ gì trong tình huống này?
   - Rủi ro pháp lý nếu không hành động?
   
4. KHUYẾN NGHỊ HÀNH ĐỘNG:
   - Bước 1: (cụ thể, khả thi)
   - Bước 2: (nếu cần)
   - Lưu ý: Chứng cứ cần thu thập

Vui lòng phân tích dựa trên khung trên và tham khảo văn bản pháp luật liên quan.
"""
    return analysis_template


@tool 
def generate_legal_document(doc_type: str, details: str) -> str:
    """
    Tạo mẫu văn bản pháp lý (đơn, hợp đồng) dựa trên yêu cầu cụ thể.
    CHỈ DÙNG khi người dùng yêu cầu soạn thảo đơn từ, hợp đồng hoặc văn bản pháp chính thức.
    KHÔNG DÙNG cho mục đích thảo luận chung.
    
    Args:
        doc_type: Loại văn bản cần tạo (đơn khiếu nại, đơn ly hôn, hợp đồng thuê nhà, v.v.)
        details: Thông tin chi tiết để điền vào mẫu
        
    Returns:
        Mẫu văn bản pháp lý hoàn chỉnh
    """
    
    # Template database
    templates = {
        "đơn khiếu nại": """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
---------------

ĐƠN KHIẾU NẠI

Kính gửi: [Cơ quan có thẩm quyền]

Tôi tên là: [Họ và tên]
Sinh ngày: [Ngày/Tháng/Năm]
Địa chỉ: [Địa chỉ cụ thể]
Số CMND/CCCD: [Số giấy tờ]

Tôi viết đơn này để khiếu nại về việc:
[Nội dung khiếu nại cụ thể]

Căn cứ pháp lý:
[Điều khoản pháp luật liên quan]

Yêu cầu:
[Yêu cầu cụ thể]

Tôi xin cam đoan nội dung trên là đúng sự thật và xin chịu trách nhiệm trước pháp luật về nội dung đơn này.

Trân trọng cảm ơn!

      Ngày ... tháng ... năm ...
      Người khiếu nại
      (Ký và ghi rõ họ tên)
""",
        "đơn xin ly hôn": """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
---------------

ĐơN YÊU CẦU LY HÔN

Kính gửi: TÒA ÁN NHÂN DÂN [Quận/Huyện]

Tôi tên là: [Họ và tên]
Sinh ngày: [Ngày/Tháng/Năm]
Nơi đăng ký hộ khẩu thường trú: [Địa chỉ]
Nơi ở hiện nay: [Địa chỉ]

Tôi và [Họ tên vợ/chồng] kết hôn ngày [Ngày/Tháng/Năm] tại [Địa điểm đăng ký kết hôn].

Hiện nay chúng tôi có [Số] con:
1. [Tên con, năm sinh]
2. ...

Lý do ly hôn:
[Mô tả ngắn gọn lý do - tình cảm không còn, mâu thuẫn không thể hòa giải...]

Về tài sản:
[Mô tả tài sản chung nếu có]

Về nuôi con:
[Đề nghị về quyền nuôi con]

Tôi đề nghị Tòa án giải quyết ly hôn cho tôi và [Tên vợ/chồng].

      Ngày ... tháng ... năm ...
      Người làm đơn
      (Ký và ghi rõ họ tên)
""",
        "hợp đồng thuê nhà": """
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
---------------

HỢP ĐỒNG THUÊ NHÀ

Hôm nay, ngày ... tháng ... năm ...
Tại: [Địa chỉ]

Chúng tôi gồm:

BÊN CHO THUÊ (Bên A):
Ông/Bà: [Họ tên]
Số CMND/CCCD: [Số]
Địa chỉ: [Địa chỉ]

BÊN THUÊ (Bên B):
Ông/Bà: [Họ tên]  
Số CMND/CCCD: [Số]
Địa chỉ: [Địa chỉ]

Hai bên thỏa thuận ký hợp đồng thuê nhà với các điều khoản sau:

ĐIỀU 1: ĐỐI TƯỢNG HỢP ĐỒNG
Bên A đồng ý cho Bên B thuê nhà tại địa chỉ: [Địa chỉ nhà cho thuê]
Diện tích: [X] m2

ĐIỀU 2: THỜI HẠN THUÊ
Thời hạn thuê: [X] tháng/năm
Từ ngày: [Ngày/Tháng/Năm]
Đến ngày: [Ngày/Tháng/Năm]

ĐIỀU 3: GIÁ THUÊ VÀ PHƯƠNG THỨC THANH TOÁN
- Giá thuê: [X] VNĐ/tháng
- Tiền đặt cọc: [X] VNĐ
- Thanh toán vào ngày [X] hàng tháng

ĐIỀU 4: TRÁCH NHIỆM CỦA CÁC BÊN
[Chi tiết trách nhiệm]

ĐIỀU 5: ĐIỀU KHOẢN KHÁC
[Các điều khoản bổ sung]

Hợp đồng được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.

    BÊN A                           BÊN B
  (Ký, ghi rõ họ tên)        (Ký, ghi rõ họ tên)
"""
    }
    
    # Get base template
    doc_type_lower = doc_type.lower()
    template = None
    
    for key in templates:
        if key in doc_type_lower:
            template = templates[key]
            break
    
    if not template:
        return f"""
Tôi sẽ giúp bạn tạo {doc_type}. Vui lòng cung cấp các thông tin sau:

THÔNG TIN CẦN THIẾT:
{details}

Dựa trên thông tin trên, tôi sẽ tạo văn bản mẫu phù hợp với yêu cầu của bạn.
Lưu ý: Văn bản này chỉ mang tính chất tham khảo, bạn nên xem xét và điều chỉnh cho phù hợp với tình huống cụ thể.
"""
    
    return f"""
{template}

HƯỚNG DẪN ĐIỀN THÔNG TIN:
Dựa trên thông tin bạn cung cấp:
{details}

Vui lòng điền các thông tin cụ thể vào các mục [...] trong mẫu trên.

LƯU Ý: 
- Văn bản này mang tính chất tham khảo
- Nên tham khảo ý kiến luật sư trước khi nộp
- Đảm bảo mọi thông tin chính xác và đầy đủ
"""


@tool
def guide_legal_procedure(procedure_name: str) -> str:
    """
    Hướng dẫn chi tiết quy trình thực hiện các thủ tục hành chính, pháp lý.
    CHỈ DÙNG khi người dùng hỏi "Làm thế nào", "Thủ tục ra sao", "Cần chuẩn bị gì" cho một vấn đề pháp lý cụ thể (ly hôn, kết hôn, kinh doanh...).
    KHÔNG DÙNG cho các yêu cầu giao tiếp thông thường.
    
    Args:
        procedure_name: Tên thủ tục cụ thể cần hướng dẫn
        
    Returns:
        Hướng dẫn từng bước với giấy tờ cần thiết và thời gian xử lý
    """
    
    # Procedure database
    procedures = {
        "ly hôn": {
            "summary": "Thủ tục ly hôn thỏa thuận hoặc đơn phương tại Tòa án",
            "steps": [
                "Bước 1: Chuẩn bị hồ sơ gồm: Đơn yêu cầu ly hôn, Giấy chứng nhận kết hôn (bản chính), Sổ hộ khẩu/CMND (bản sao), Giấy khai sinh của con (nếu có)",
                "Bước 2: Nộp hồ sơ tại Tòa án nơi đương sự cư trú",
                "Bước 3: Tòa án thụ lý hồ sơ (trong vòng 7 ngày)",
                "Bước 4: Hòa giải (bắt buộc - 1 lần, có thể 2 lần)",
                "Bước 5: Xét xử (nếu hòa giải không thành)",
                "Bước 6: Nhận bản án ly hôn (có hiệu lực sau 15 ngày nếu không kháng cáo)",
                "Bước 7: Đăng ký ly hôn tại UBND (nếu ly hôn thỏa thuận)"
            ],
            "documents": [
                "Đơn yêu cầu ly hôn (02 bản)",
                "Giấy chứng nhận kết hôn (bản chính)",
                "Sổ hộ khẩu, CMND/CCCD (bản sao công chứng)",
                "Giấy khai sinh của con (bản sao)",
                "Giấy tờ về tài sản chung (nếu có)"
            ],
            "time": "3-6 tháng (ly hôn tranh chấp), 1-2 tháng (ly hôn thỏa thuận)",
            "cost": "Phí tòa án: 200,000-500,000 VNĐ",
            "notes": "Nếu ly hôn thỏa thuận, có thể đăng ký trực tiếp tại UBND mà không qua Tòa án"
        },
        "đăng ký kết hôn": {
            "summary": "Thủ tục đăng ký kết hôn tại UBND phường/xã",
            "steps": [
                "Bước 1: Chuẩn bị hồ sơ",
                "Bước 2: Nộp hồ sơ tại UBND nơi một trong hai bên cư trú",
                "Bước 3: UBND kiểm tra hồ sơ",
                "Bước 4: Tổ chức đăng ký kết hôn (sau ít nhất 3 ngày làm việc)",
                "Bước 5: Nhận Giấy chứng nhận kết hôn"
            ],
            "documents": [
                "Giấy tờ tùy thân (CMND/CCCD, Hộ chiếu)",
                "Giấy xác nhận tình trạng hôn nhân",
                "Giấy khám sức khỏe (nếu yêu cầu)",
                "Hộ khẩu (bản sao)"
            ],
            "time": "3-7 ngày làm việc",
            "cost": "Miễn phí hoặc 10,000-50,000 VNĐ (tùy địa phương)",
            "notes": "Cả hai bên phải có mặt khi đăng ký. Tuổi kết hôn tối thiểu: Nam 20, Nữ 18"
        },
        "đăng ký kinh doanh": {
            "summary": "Thủ tục đăng ký doanh nghiệp/hộ kinh doanh",
            "steps": [
                "Bước 1: Chuẩn bị hồ sơ đăng ký",
                "Bước 2: Nộp hồ sơ trực tuyến qua Cổng thông tin quốc gia hoặc trực tiếp tại Phòng Đăng ký kinh doanh",
                "Bước 3: Thanh toán phí (nếu có)",
                "Bước 4: Nhận Giấy chứng nhận đăng ký doanh nghiệp",
                "Bước 5: Khắc dấu, mở tài khoản ngân hàng",
                "Bước 6: Đăng ký thuế, bảo hiểm xã hội"
            ],
            "documents": [
                "Giấy đề nghị đăng ký doanh nghiệp",
                "Điều lệ công ty (đối với công ty)",
                "Danh sách thành viên/cổ đông",
                "CMND/CCCD của người đại diện pháp luật",
                "Giấy tờ về trụ sở (hợp đồng thuê hoặc giấy tờ sở hữu)"
            ],
            "time": "3-5 ngày làm việc",
            "cost": "Hộ kinh doanh: ~40,000-100,000 VNĐ; Công ty: ~300,000-500,000 VNĐ",
            "notes": "Có thể đăng ký trực tuyến 100% qua https://dangkykinhdoanh.gov.vn"
        },
        "giấy phép lái xe": {
            "summary": "Thủ tục cấp mới/đổi Giấy phép lái xe (GPLX)",
            "steps": [
                "Bước 1: Chuẩn bị hồ sơ (khám sức khỏe lái xe tại cơ sở y tế có thẩm quyền)",
                "Bước 2: Nộp hồ sơ trực tuyến qua Cổng dịch vụ công Quốc gia (dichvucong.gov.vn) hoặc trực tiếp tại Sở GTVT/Trung tâm hành chính công",
                "Bước 3: Chụp ảnh trực tiếp và đóng lệ phí",
                "Bước 4: Nhận giấy hẹn trả kết quả",
                "Bước 5: Nhận GPLX mới (trả trực tiếp hoặc qua bưu điện)"
            ],
            "documents": [
                "Đơn đề nghị đổi/cấp lại GPLX (theo mẫu)",
                "Giấy khám sức khỏe lái xe điện tử (hoặc bản giấy)",
                "GPLX cũ (nếu đổi)",
                "CCCD/CMND (bản chính để đối chiếu)",
                "Ảnh chân dung (chụp tại nơi làm thủ tục)"
            ],
            "time": "5 ngày làm việc (đổi GPLX), 10 ngày (cấp lại)",
            "cost": "135,000 VNĐ (lệ phí cấp GPLX) + Phí khám sức khỏe (~300k)",
            "notes": "Nếu đổi GPLX mức độ 4 online, cần có tài khoản VNeID và Giấy khám sức khỏe lái xe điện tử"
        }
    }
    
    # Search for procedure (Robust matching)
    procedure_key = None
    query_norm = procedure_name.lower().strip()
    
    # Direct mapping for common aliases
    aliases = {
        "bằng lái": "giấy phép lái xe",
        "bằng lái xe": "giấy phép lái xe",
        "gplx": "giấy phép lái xe",
        "kết hôn": "đăng ký kết hôn",
        "cưới": "đăng ký kết hôn",
        "công ty": "đăng ký kinh doanh",
        "doanh nghiệp": "đăng ký kinh doanh",
        "hộ kinh doanh": "đăng ký kinh doanh"
    }
    
    # Check aliases first
    for alias, target in aliases.items():
        if alias in query_norm:
            procedure_key = target
            break
            
    # Then check main keys
    if not procedure_key:
        for key in procedures:
            if key in query_norm:
                procedure_key = key
                break
    
    if not procedure_key:
        return f"""
Rất tiếc, tôi chưa có thông tin chi tiết về thủ tục "{procedure_name}".

CÁC THỦ TỤC HIỆN CÓ HƯỚNG DẪN:
- Ly hôn
- Đăng ký kết hôn
- Đăng ký kinh doanh
- Cấp/Đổi Giấy phép lái xe

Vui lòng chọn một trong các thủ tục trên hoặc tôi có thể tìm kiếm thông tin pháp luật liên quan.
"""
    
    proc = procedures[procedure_key]
    
    result = f"""
📋 HƯỚNG DẪN: {proc['summary'].upper()}

CÁC BƯỚC THỰC HIỆN:
"""
    for step in proc['steps']:
        result += f"\n{step}"
    
    result += "\n\n📄 HỒ SƠ CẦN CHUẨN BỊ:\n"
    for doc in proc['documents']:
        result += f"• {doc}\n"
    
    result += f"\n⏱️ THỜI GIAN XỬ LÝ: {proc['time']}"
    result += f"\n💰 CHI PHÍ: {proc['cost']}"
    result += f"\n\n⚠️ LƯU Ý: {proc['notes']}"
    
    return result
