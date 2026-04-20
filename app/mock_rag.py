from __future__ import annotations

import random
import time

from .incidents import STATE

# Tỷ lệ RAG trả về không tìm thấy (10%)
EMPTY_RESULT_RATE = 0.10
# Tỷ lệ RAG throw lỗi ngẫu nhiên (3%)
RAG_ERROR_RATE = 0.03

CORPUS: dict[str, list[str]] = {
    # Mathematics
    "phương trình bậc 2": [
        "Phương trình bậc hai ax² + bx + c = 0 có delta = b² - 4ac.",
        "Nếu delta > 0: hai nghiệm phân biệt x = (-b ± √delta) / 2a.",
        "Nếu delta = 0: nghiệm kép x = -b / 2a.",
        "Nếu delta < 0: vô nghiệm thực.",
    ],
    "đạo hàm": [
        "Đạo hàm của xⁿ là n·xⁿ⁻¹.",
        "Đạo hàm của sin(x) là cos(x); đạo hàm của cos(x) là -sin(x).",
        "Quy tắc tích: (f·g)' = f'·g + f·g'.",
        "Quy tắc thương: (f/g)' = (f'·g - f·g') / g².",
    ],
    "tích phân": [
        "Tích phân là phép toán ngược của đạo hàm.",
        "∫xⁿ dx = xⁿ⁺¹/(n+1) + C với n ≠ -1.",
        "∫sin(x) dx = -cos(x) + C.",
        "Định lý Newton-Leibniz: ∫[a,b] f(x)dx = F(b) - F(a).",
    ],
    "hình học": [
        "Diện tích hình tròn: S = π·r²; Chu vi: C = 2π·r.",
        "Thể tích hình cầu: V = (4/3)·π·r³.",
        "Định lý Pythagoras: a² + b² = c².",
        "Diện tích tam giác: S = (1/2)·đáy·chiều cao.",
    ],
    "xác suất": [
        "Xác suất của biến cố A: P(A) = số kết quả thuận lợi / tổng số kết quả.",
        "Xác suất bù: P(Ā) = 1 - P(A).",
        "Xác suất cộng: P(A∪B) = P(A) + P(B) - P(A∩B).",
        "Xác suất nhân (độc lập): P(A∩B) = P(A)·P(B).",
    ],
    # Literature
    "văn học": [
        "Truyện Kiều là tác phẩm của Nguyễn Du, gồm 3254 câu thơ lục bát.",
        "Chí Phèo của Nam Cao phản ánh bi kịch tha hóa của người nông dân.",
        "Các biện pháp tu từ: so sánh, ẩn dụ, nhân hóa, điệp ngữ, hoán dụ.",
        "Phân tích nhân vật cần chú ý: ngoại hình, tính cách, hành động, tư tưởng.",
    ],
    "tập làm văn": [
        "Bài văn nghị luận: mở bài, thân bài (luận điểm + luận cứ + lập luận), kết bài.",
        "Văn miêu tả: chi tiết cụ thể, hình ảnh sinh động, cảm xúc người viết.",
        "Mở bài trực tiếp: nêu thẳng vấn đề. Gián tiếp: dẫn dắt rồi vào vấn đề.",
    ],
    # Physics
    "vật lý": [
        "Định luật Newton I: Vật giữ nguyên trạng thái nếu không có lực tác dụng.",
        "Định luật Newton II: F = m·a.",
        "Động lượng p = m·v; Xung lực = Δp.",
        "Công thức động năng: Eđ = ½m·v².",
    ],
    "điện học": [
        "Định luật Ohm: U = I·R.",
        "Công suất điện: P = U·I = I²·R = U²/R.",
        "Điện trở nối tiếp: R_tổng = R₁ + R₂.",
        "Điện trở song song: 1/R_tổng = 1/R₁ + 1/R₂.",
    ],
    "quang học": [
        "Định luật phản xạ: góc phản xạ = góc tới.",
        "Định luật Snell (khúc xạ): n₁·sin(i) = n₂·sin(r).",
        "Thấu kính hội tụ có tiêu cự f > 0.",
        "Công thức thấu kính: 1/f = 1/d + 1/d'.",
    ],
    # Chemistry
    "hóa học": [
        "Bảng tuần hoàn có 118 nguyên tố, sắp xếp theo số proton tăng dần.",
        "Phản ứng oxi hóa-khử: chất khử nhường electron, chất oxi hóa nhận electron.",
        "Axit-bazơ: Axit cho H⁺, bazơ nhận H⁺ (Brønsted-Lowry).",
        "Tốc độ phản ứng tăng khi: tăng nhiệt độ, tăng nồng độ, dùng xúc tác.",
    ],
    # English
    "tiếng anh": [
        "12 thì trong tiếng Anh bao gồm các thì hiện tại, quá khứ và tương lai.",
        "Câu bị động: S + be + V_pp + (by O).",
        "Mệnh đề quan hệ: who (người), which (vật), that (người/vật).",
        "Reported speech: lùi thì và đổi đại từ khi chuyển sang câu gián tiếp.",
    ],
    # History
    "lịch sử": [
        "Cách mạng tháng Tám 1945: nhân dân Việt Nam giành độc lập.",
        "Chiến dịch Điện Biên Phủ (1954): kết thúc kháng chiến chống Pháp.",
        "30/4/1975: Giải phóng miền Nam, thống nhất đất nước.",
        "Đổi mới 1986: chuyển sang kinh tế thị trường định hướng XHCN.",
    ],
    # Biology
    "sinh học": [
        "Tế bào là đơn vị cơ bản của sự sống.",
        "ADN mang thông tin di truyền, cấu trúc xoắn kép.",
        "Quá trình quang hợp: 6CO₂ + 6H₂O + ánh sáng → C₆H₁₂O₆ + 6O₂.",
        "Đột biến gen là sự thay đổi trong cấu trúc gen.",
    ],
}


def retrieve(message: str) -> list[str]:
    # ── Incident: tool_fail ────────────────────────────────────
    if STATE["tool_fail"]:
        raise RuntimeError("Knowledge base retriever timeout — vector store unreachable")

    # ── Incident: rag_slow ─────────────────────────────────────
    if STATE["rag_slow"]:
        time.sleep(2.5)

    # ── Random RAG error (3%) ──────────────────────────────────
    if random.random() < RAG_ERROR_RATE:
        raise ConnectionError("Knowledge base connection pool exhausted")

    lowered = message.lower()

    # Exact key match
    for key, docs in CORPUS.items():
        if key in lowered:
            return docs

    # Multi-keyword partial match
    for key, docs in CORPUS.items():
        if any(word in lowered for word in key.split()):
            return docs[:2]

    # Random empty result (10%) — tests fallback behavior
    if random.random() < EMPTY_RESULT_RATE:
        return []

    return ["Không tìm thấy tài liệu phù hợp. Hãy thử hỏi về: toán, văn, lý, hóa, anh, sử, sinh."]
