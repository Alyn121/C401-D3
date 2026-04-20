from __future__ import annotations

import random
import time

from .incidents import STATE

# Tỷ lệ lỗi ngẫu nhiên từ hạ tầng (3%)
RAG_INFRA_ERROR_RATE = 0.03
# Tỷ lệ không tìm thấy tài liệu (8%)
EMPTY_RESULT_RATE = 0.08

CORPUS: dict[str, list[str]] = {
    # ── Toán ─────────────────────────────────────────────────────
    "phương trình bậc 2": [
        "Phương trình bậc hai ax² + bx + c = 0 có delta = b² - 4ac.",
        "Nếu delta > 0: hai nghiệm phân biệt x = (-b ± √delta) / 2a.",
        "Nếu delta = 0: nghiệm kép x = -b / 2a.",
        "Nếu delta < 0: vô nghiệm thực.",
    ],
    "hệ phương trình": [
        "Giải hệ phương trình bằng phương pháp thế hoặc phương pháp cộng.",
        "Ví dụ: 2x + y = 5 và x - y = 1 → cộng 2 phương trình: 3x = 6 → x = 2, y = 1.",
        "Hệ có nghiệm duy nhất, vô số nghiệm hoặc vô nghiệm.",
    ],
    "đạo hàm": [
        "Đạo hàm của xⁿ là n·xⁿ⁻¹.",
        "Đạo hàm của sin(x) là cos(x); đạo hàm của cos(x) là -sin(x).",
        "Quy tắc tích: (f·g)' = f'·g + f·g'. Quy tắc thương: (f/g)' = (f'g - fg') / g².",
        "Ví dụ: y = x³ - 4x + 1 → y' = 3x² - 4.",
    ],
    "tích phân": [
        "Tích phân là phép toán ngược của đạo hàm.",
        "∫xⁿ dx = xⁿ⁺¹/(n+1) + C với n ≠ -1.",
        "Định lý Newton-Leibniz: ∫[a,b] f(x)dx = F(b) - F(a).",
    ],
    "xác suất": [
        "Xác suất P(A) = số kết quả thuận lợi / tổng số kết quả.",
        "Tung đồng xu 3 lần: P(3 mặt ngửa) = (1/2)³ = 1/8.",
        "Xác suất nhân (độc lập): P(A∩B) = P(A)·P(B).",
    ],
    "hình học": [
        "Diện tích hình tròn: S = π·r². Ví dụ: r=5cm → S = 25π ≈ 78.54 cm².",
        "Chu vi hình tròn: C = 2π·r.",
        "Định lý Pythagoras: a² + b² = c² (tam giác vuông).",
        "Tam giác cân: 2 cạnh bên bằng nhau, góc ở đáy bằng nhau.",
    ],
    "cấp số": [
        "Cấp số cộng: dãy số có công sai d không đổi. Ví dụ: 1, 3, 5, 7... (d=2).",
        "Số hạng tổng quát: aₙ = a₁ + (n-1)·d.",
        "Cấp số nhân: dãy số có công bội q không đổi.",
    ],
    "logarit": [
        "Logarit: log_a(b) = x ↔ aˣ = b (điều kiện: a > 0, a ≠ 1, b > 0).",
        "log_a(x·y) = log_a(x) + log_a(y).",
        "Đổi cơ số: log_a(b) = log_c(b) / log_c(a).",
    ],
    "bất phương trình": [
        "Giải bất phương trình bậc nhất: ax + b > 0 (đổi chiều khi nhân/chia số âm).",
        "Ví dụ: 2x - 3 > 5 → 2x > 8 → x > 4.",
        "Bất phương trình bậc 2: ax² + bx + c > 0, xét dấu theo delta.",
    ],
    # ── Vật lý ───────────────────────────────────────────────────
    "vật lý": [
        "Định luật Newton II: F = m·a (lực = khối lượng × gia tốc).",
        "Ví dụ: F = 20N, m = 5kg → a = F/m = 4 m/s².",
        "Động năng: Eđ = ½m·v². Ví dụ: m=5kg, v=10m/s → Eđ = 250J.",
    ],
    "vận tốc": [
        "Vận tốc trung bình: v = s/t (quãng đường / thời gian).",
        "Ví dụ: s=120km, t=2h → v = 60 km/h.",
        "Chuyển động đều: vận tốc không đổi theo thời gian.",
    ],
    "điện học": [
        "Định luật Ohm: U = I·R.",
        "Công suất điện: P = U·I = I²·R = U²/R.",
        "Điện trở song song: 1/R_tg = 1/R₁ + 1/R₂.",
    ],
    "cảm ứng điện từ": [
        "Hiện tượng cảm ứng điện từ: khi từ thông qua mạch thay đổi → xuất hiện dòng điện cảm ứng.",
        "Ứng dụng: máy phát điện, máy biến áp, động cơ điện.",
        "Định luật Faraday: suất điện động tỷ lệ với tốc độ biến thiên từ thông.",
    ],
    "quang học": [
        "Định luật phản xạ: góc phản xạ = góc tới.",
        "Gương phẳng: ảnh ảo, đối xứng qua gương, bằng vật.",
        "Định luật khúc xạ (Snell): n₁·sin(i) = n₂·sin(r).",
    ],
    "âm học": [
        "Âm phản xạ (tiếng vang): xảy ra khi âm gặp vật cản và bị phản lại.",
        "Điều kiện tiếng vang: thời gian âm phản xạ đến tai dài hơn 1/15 giây so với âm phát.",
        "Khoảng cách tối thiểu để nghe tiếng vang ≈ 17m.",
    ],
    # ── Hóa học ──────────────────────────────────────────────────
    "hóa học": [
        "Cân bằng phương trình: 4Fe + 3O₂ → 2Fe₂O₃.",
        "Số mol: n = V/22.4 (ở đktc). Ví dụ: 11.2L O₂ → n = 0.5 mol.",
        "Phản ứng trung hòa: axit + bazơ → muối + nước. HCl + NaOH → NaCl + H₂O.",
    ],
    "axit bazơ": [
        "Axit mạnh (HCl, H₂SO₄, HNO₃): phân li hoàn toàn trong nước.",
        "Axit yếu (CH₃COOH, H₂CO₃): chỉ phân li một phần.",
        "Bazơ mạnh (NaOH, KOH): phân li hoàn toàn.",
    ],
    "este": [
        "Este là sản phẩm của phản ứng axit + ancol, có nhóm chức -COO-.",
        "Ứng dụng: hương liệu thực phẩm (mùi chuối, dứa), dung môi, nhựa.",
        "Phản ứng thủy phân este trong môi trường axit/bazơ.",
    ],
    "oxi hóa khử": [
        "Chất khử nhường electron, chất oxi hóa nhận electron.",
        "Cân bằng Fe + HCl → FeCl₂ + H₂: Fe → Fe²⁺ + 2e⁻ (oxi hóa).",
        "H₂SO₄ đặc (ứng dụng CN): sản xuất phân bón, acquy, tẩy gỉ sắt.",
    ],
    # ── Sinh học ─────────────────────────────────────────────────
    "sinh học": [
        "Tế bào là đơn vị cơ bản của sự sống.",
        "ADN cấu trúc xoắn kép, mang thông tin di truyền.",
        "Quang hợp: 6CO₂ + 6H₂O + ánh sáng → C₆H₁₂O₆ + 6O₂.",
    ],
    "quang hợp": [
        "Quang hợp chuyển năng lượng ánh sáng thành năng lượng hóa học.",
        "Phương trình: 6CO₂ + 6H₂O + hν → C₆H₁₂O₆ + 6O₂.",
        "Diệp lục (chlorophyll) hấp thụ ánh sáng đỏ và xanh tím.",
        "Quan trọng: tạo O₂ cho khí quyển, cơ sở chuỗi thức ăn.",
    ],
    # ── Văn học ──────────────────────────────────────────────────
    "văn học": [
        "Truyện Kiều của Nguyễn Du: 3254 câu lục bát, giá trị nhân đạo và hiện thực sâu sắc.",
        "Chí Phèo của Nam Cao: bi kịch tha hóa, không được xã hội công nhận.",
        "Vợ chồng A Phủ (Tô Hoài): nhân vật Mị — sức sống tiềm tàng, bị áp bức nhưng vươn lên.",
        "Tây Tiến (Quang Dũng): hình tượng người lính lãng mạn, bi tráng.",
    ],
    "tập làm văn": [
        "Bài nghị luận: mở bài → thân bài (luận điểm + dẫn chứng + phân tích) → kết bài.",
        "Bài văn hoàn chỉnh cần: bố cục, lập luận chặt chẽ, dẫn chứng cụ thể.",
        "Viết hộ hoàn chỉnh không được (gian lận học thuật), chỉ hỗ trợ dàn ý.",
    ],
    # ── Lịch sử ──────────────────────────────────────────────────
    "lịch sử": [
        "Cách mạng tháng Tám 1945: nhân dân Việt Nam giành độc lập, thành lập VNDCCH.",
        "Chiến dịch Điện Biên Phủ (1954): kết thúc kháng chiến chống Pháp.",
        "30/4/1975: Giải phóng miền Nam. Chiến tranh thế giới I (1914–1918): do mâu thuẫn các đế quốc.",
    ],
    # ── Địa lý ───────────────────────────────────────────────────
    "địa lý": [
        "Khí hậu nhiệt đới gió mùa VN: nóng ẩm, mưa nhiều, có 2 mùa mưa-khô.",
        "ĐBSCL: đất phù sa màu mỡ, khí hậu nóng ẩm → lợi thế trồng lúa, trái cây, nuôi thủy sản.",
        "Địa hình VN: 3/4 đồi núi, đồng bằng chiếm 1/4, bờ biển dài 3260km.",
    ],
    # ── Tiếng Anh ────────────────────────────────────────────────
    "tiếng anh": [
        "Hiện tại đơn (Simple Present): dùng cho thói quen, sự thật. Ví dụ: She goes to school.",
        "Hiện tại tiếp diễn (Present Continuous): đang xảy ra. Ví dụ: She is going to school.",
        "Much (không đếm được): much water. Many (đếm được): many books.",
        "Câu bị động: S + be + V³ + (by O). Ví dụ: The book is read by her.",
    ],
}

# ── Danh sách từ khóa ngoài phạm vi môn học ──────────────────────
OUT_OF_SCOPE_KEYWORDS = [
    "nấu", "nấu ăn", "công thức nấu", "bò kho", "phở", "bún",
    "chứng khoán", "đầu tư", "bitcoin", "crypto",
    "game", "phim", "âm nhạc",
    "thời tiết", "tin tức",
]

DANGEROUS_KEYWORDS = [
    "chế tạo pháo", "thuốc nổ", "vũ khí", "bom", "chất độc",
    "gây bỏng", "gây chết người", "tự tử", "tự làm hại",
    "pha thuốc tẩy với axit", "khí độc",
]


def retrieve(message: str) -> list[str]:
    # ── Incident: tool_fail ────────────────────────────────────
    if STATE["tool_fail"]:
        raise RuntimeError("Knowledge base retriever timeout — vector store unreachable")

    # ── Incident: rag_slow ─────────────────────────────────────
    if STATE["rag_slow"]:
        time.sleep(2.5)

    # ── Random infrastructure error (3%) ──────────────────────
    if random.random() < RAG_INFRA_ERROR_RATE:
        raise ConnectionError("Knowledge base connection pool exhausted")

    # ── Safety: nội dung nguy hiểm → trả về rỗng (LLM sẽ từ chối) ──
    lowered = message.lower().strip()
    for kw in DANGEROUS_KEYWORDS:
        if kw in lowered:
            return []  # không cung cấp tài liệu cho nội dung nguy hiểm

    # ── Empty / nonsense input ────────────────────────────────
    if len(lowered) < 3:
        return []

    # ── Out of scope ──────────────────────────────────────────
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if kw in lowered:
            return []

    # ── Exact corpus key match ────────────────────────────────
    for key, docs in CORPUS.items():
        if key in lowered:
            return docs

    # ── Partial keyword match ─────────────────────────────────
    for key, docs in CORPUS.items():
        if any(word in lowered for word in key.split() if len(word) > 2):
            return docs[:2]

    # ── Random empty (8%) ─────────────────────────────────────
    if random.random() < EMPTY_RESULT_RATE:
        return []

    return ["Không tìm thấy tài liệu phù hợp. Hỗ trợ: toán, vật lý, hóa học, sinh học, văn học, lịch sử, địa lý, tiếng Anh."]
