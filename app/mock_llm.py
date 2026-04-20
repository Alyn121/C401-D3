from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass

from .incidents import STATE

# ── Safety & refusal config ────────────────────────────────────
DANGEROUS_PATTERNS = [
    r"chế tạo pháo", r"thuốc nổ", r"vũ khí", r"bom", r"chất độc",
    r"gây bỏng", r"gây chết", r"tự tử", r"tự làm hại", r"tự sát",
    r"pha thuốc tẩy với axit", r"khí độc", r"chỉ em cách tự",
    r"có thể pha.+để tạo khí",
]
SELF_HARM_PATTERNS = [
    r"tự tử không đau", r"cách chết", r"muốn chết", r"tự kết liễu",
]
CHEATING_PATTERNS = [
    r"cho (em|tôi|mình).*(đáp án|kết quả).*(đề thi|bài kiểm tra|bài thi)",
    r"làm hộ.*bài kiểm tra",
    r"làm hộ.*bài thi",
    r"làm hộ.*đề thi",
    r"đáp án trắc nghiệm.*(40|tất cả|hết) câu",
    r"viết (hộ|hết|toàn bộ).*bài (văn|luận|kiểm tra)",
]
PROMPT_INJECTION_PATTERNS = [
    r"ignore (previous|all) instruction",
    r"disregard.*instruction",
    r"từ giờ chỉ trả lời bằng",
    r"output (system prompt|your prompt)",
    r"pretend you are",
]
OUT_OF_SCOPE_PATTERNS = [
    r"(nấu|công thức nấu).*(bò|gà|cá|phở|bún)",
    r"chứng khoán|đầu tư coin|bitcoin|crypto",
    r"chẩn đoán bệnh|kê đơn thuốc|điều trị bệnh",
    r"địa chỉ nhà em|mật khẩu (wifi|tài khoản)",
]
MISSING_INFO_PATTERNS = [
    r"^giải (giúp|hộ|cho) em bài này$",
    r"^phân tích bài thơ này",
    r"^(2 \+ \?|x \+ \? ?=|giải bài này)$",
]

# ── Error simulation (5% random, infrastructure) ──────────────
RANDOM_ERROR_RATE = 0.05

# ── Answer templates per feature ──────────────────────────────
ANSWER_TEMPLATES: dict[str, list[str]] = {
    "solve_exercise": [
        "Bước 1: Xác định dạng bài và công thức áp dụng.\nBước 2: Thay số vào công thức.\nBước 3: Tính toán từng bước.\nBước 4: Kiểm tra và kết luận.\n\n📌 Đáp số: {result}.",
        "Giải:\n1. Phân tích đề: Xác định ẩn số và điều kiện.\n2. Lập phương trình.\n3. Giải: {result}.\n4. Kết luận.",
        "Áp dụng công thức đã học:\n- Bước 1: Tính các đại lượng trung gian.\n- Bước 2: Thay vào biểu thức.\n- Kết quả: {result}.",
    ],
    "explain_concept": [
        "📖 Định nghĩa:\nĐây là một khái niệm quan trọng trong chương trình học.\n\n🔑 Tính chất chính:\n  • Tính chất 1: Áp dụng trong trường hợp cụ thể.\n  • Tính chất 2: Liên quan đến công thức tính toán.\n\n💡 Ví dụ minh họa: Bài toán cụ thể minh họa khái niệm này.\n\n⚠️ Lưu ý: Điểm dễ nhầm lẫn khi làm bài.",
        "Để hiểu rõ chủ đề này:\n1️⃣ Khái niệm cơ bản: Định nghĩa và phạm vi áp dụng.\n2️⃣ Công thức / Quy tắc cần ghi nhớ.\n3️⃣ Ví dụ áp dụng thực tế.\n4️⃣ Lưu ý quan trọng khi làm bài kiểm tra.",
    ],
    "generate_quiz": [
        "📝 Bài tập luyện:\n\nCâu 1 (Dễ - 2đ): Phát biểu định nghĩa và nêu 2 ví dụ.\nCâu 2 (Trung bình - 3đ): Tính giá trị biểu thức cho trước.\nCâu 3 (Khó - 5đ): Chứng minh tính chất và áp dụng vào bài toán thực tế.\n\n⏱ Thời gian: 20 phút | Không tài liệu.",
        "🎯 Bộ câu hỏi ôn tập:\n\n[TRẮC NGHIỆM]\n1. Khẳng định nào ĐÚNG?\n   A. ...  B. ...  C. ...  D. ...\n\n[TỰ LUẬN]\n2. Giải bài toán sau đầy đủ các bước:\n   Cho ... Tìm ...",
    ],
    "grade_essay": [
        "📊 Nhận xét bài làm:\n\n✅ Điểm mạnh:\n  • Bố cục rõ ràng, đủ mở - thân - kết.\n  • Luận điểm chặt chẽ, có dẫn chứng.\n\n⚠️ Điểm cần cải thiện:\n  • Cần thêm dẫn chứng cụ thể hơn.\n  • Kết bài chưa đủ súc tích.\n\n📝 Điểm ước tính: 7.5/10\n💡 Gợi ý: Bổ sung trích dẫn từ tác phẩm gốc.",
    ],
    "qa": [
        "Dựa trên tài liệu tham khảo:\n{answer}\n\n📚 Đây là kiến thức trọng tâm trong chương trình. Bạn có muốn làm bài tập luyện không?",
        "Theo sách giáo khoa:\n{answer}\n\n💡 Lưu ý quan trọng khi thi: Trình bày đầy đủ các bước và đơn vị.",
    ],
    "summary": [
        "📋 Tóm tắt nội dung trọng tâm:\n\n• Điểm 1: Khái niệm và định nghĩa cốt lõi.\n• Điểm 2: Công thức và quy tắc quan trọng.\n• Điểm 3: Ứng dụng thực tế và ví dụ điển hình.\n• Điểm 4: Lưu ý khi làm bài thi.\n\n🔥 Nội dung này thường xuất hiện trong đề thi THPT Quốc gia.",
    ],
}

# ── Refusal messages per case_type ────────────────────────────
REFUSAL_MESSAGES = {
    "dangerous": (
        "⛔ Mình không thể hỗ trợ yêu cầu này vì nó liên quan đến nội dung nguy hiểm "
        "có thể gây hại cho bản thân hoặc người khác. "
        "Nếu bạn cần thông tin học thuật liên quan, hãy hỏi theo hướng khác."
    ),
    "self_harm": (
        "💙 Mình lo lắng cho bạn. Nếu bạn đang gặp khó khăn, hãy liên hệ đường dây hỗ trợ "
        "sức khỏe tâm thần: **1800 599 920** (miễn phí, 24/7). "
        "Mình luôn ở đây để hỗ trợ học tập khi bạn sẵn sàng. 💙"
    ),
    "cheating": (
        "🚫 Mình không thể cung cấp đáp án gian lận hoặc làm bài hộ hoàn toàn. "
        "Điều này không giúp bạn thực sự học được kiến thức. "
        "Mình có thể: hướng dẫn từng bước, giải thích khái niệm, hoặc tạo bài tập luyện tương tự."
    ),
    "out_of_scope": (
        "📚 Câu hỏi này nằm ngoài phạm vi hỗ trợ học tập của mình. "
        "Mình chuyên hỗ trợ các môn học: Toán, Vật lý, Hóa học, Sinh học, "
        "Văn học, Lịch sử, Địa lý và Tiếng Anh. "
        "Bạn có câu hỏi nào về các môn học này không?"
    ),
    "prompt_injection": (
        "⚠️ Mình nhận thấy yêu cầu cố gắng thay đổi cách mình hoạt động. "
        "Mình chỉ hỗ trợ học tập theo đúng chức năng. "
        "Nếu có câu hỏi học thuật hợp lệ, mình rất sẵn lòng giúp!"
    ),
    "missing_info": (
        "🤔 Câu hỏi của bạn chưa đủ thông tin để mình có thể hỗ trợ. "
        "Vui lòng cung cấp thêm: tên bài tập / đề bài cụ thể / môn học và chủ đề. "
        "Ví dụ: 'Giải phương trình bậc 2: x² - 5x + 6 = 0, môn Toán lớp 11'."
    ),
    "medical": (
        "🏥 Mình không thể chẩn đoán bệnh hay tư vấn y tế. "
        "Nếu bạn có triệu chứng bất thường, hãy đến cơ sở y tế ngay lập tức. "
        "Trường hợp khẩn cấp: gọi **115**."
    ),
    "empty": (
        "❓ Mình chưa nhận được nội dung câu hỏi. "
        "Bạn vui lòng gửi lại với đầy đủ nội dung câu hỏi nhé!"
    ),
    "gibberish": (
        "🤷 Mình không hiểu câu hỏi này. "
        "Bạn có thể viết lại rõ ràng hơn không? "
        "Hãy đặt câu hỏi theo dạng: '[Môn học] — [Câu hỏi cụ thể]'."
    ),
    "sensitive_credential": (
        "🔒 Lưu ý: Mình không lưu trữ bất kỳ thông tin cá nhân nào bạn chia sẻ "
        "(mật khẩu, địa chỉ, số tài khoản...). "
        "Bạn không nên chia sẻ những thông tin nhạy cảm này trong bất kỳ ứng dụng nào. "
        "Nếu câu hỏi học tập của bạn là: "
    ),
    "ghostwriting": (
        "✏️ Mình không thể viết hộ bài luận hoàn chỉnh để nộp — đây là hành vi gian lận học thuật. "
        "Tuy nhiên mình có thể: lập dàn ý chi tiết, góp ý từng đoạn, "
        "hoặc giải thích các ý cần triển khai. Bạn muốn bắt đầu từ đâu?"
    ),
}


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model

    def generate(self, prompt: str) -> FakeResponse:
        time.sleep(0.15)

        # ── Incident: cost_spike ───────────────────────────────
        input_tokens  = max(20, len(prompt) // 4)
        output_tokens = random.randint(120, 280)
        if STATE["cost_spike"]:
            output_tokens *= 4

        # Tách message gốc từ prompt (format: "...Question=<msg>")
        msg = self._extract_message(prompt)
        feature = self._detect_feature(prompt)

        # ── Kiểm tra safety theo thứ tự ưu tiên ──────────────

        # 1. Nội dung tự làm hại bản thân — ưu tiên cao nhất
        if self._match_any(msg, SELF_HARM_PATTERNS):
            return self._make_response(REFUSAL_MESSAGES["self_harm"], input_tokens, 80)

        # 2. Nội dung nguy hiểm
        if self._match_any(msg, DANGEROUS_PATTERNS):
            return self._make_response(REFUSAL_MESSAGES["dangerous"], input_tokens, 80)

        # 3. Gian lận học thuật
        if self._match_any(msg, CHEATING_PATTERNS):
            return self._make_response(REFUSAL_MESSAGES["cheating"], input_tokens, 100)

        # 4. Prompt injection
        if self._match_any(msg, PROMPT_INJECTION_PATTERNS):
            # Prompt injection nhẹ: vẫn trả lời câu hỏi thật nhưng cảnh báo
            real_q = self._strip_injection(msg)
            if real_q and len(real_q) > 10:
                answer = self._gen_answer(feature, real_q, prompt)
                return self._make_response(
                    f"⚠️ Lưu ý: Mình không thể thay đổi cách hoạt động theo yêu cầu đó.\n\n{answer}",
                    input_tokens, output_tokens
                )
            return self._make_response(REFUSAL_MESSAGES["prompt_injection"], input_tokens, 70)

        # 5. Ngoài phạm vi
        if self._match_any(msg, OUT_OF_SCOPE_PATTERNS):
            # Nếu có câu hỏi hợp lệ đi kèm thông tin nhạy cảm
            if "mật khẩu" in msg.lower() or "địa chỉ nhà" in msg.lower():
                return self._make_response(
                    REFUSAL_MESSAGES["sensitive_credential"] + self._extract_real_question(msg),
                    input_tokens, 90
                )
            if "chẩn đoán" in msg.lower() or "bác sĩ" in msg.lower() or "đau" in msg.lower():
                return self._make_response(REFUSAL_MESSAGES["medical"], input_tokens, 80)
            return self._make_response(REFUSAL_MESSAGES["out_of_scope"], input_tokens, 80)

        # 6. Ghostwriting
        if re.search(r"viết (hộ|giúp|cho).{0,20}bài (văn|luận).{0,30}(nộp|đầy đủ|hoàn chỉnh)", msg.lower()):
            return self._make_response(REFUSAL_MESSAGES["ghostwriting"], input_tokens, 100)

        # 7. Thiếu thông tin / câu hỏi mơ hồ
        if self._match_any(msg, MISSING_INFO_PATTERNS) or len(msg.strip()) < 5:
            if len(msg.strip()) == 0:
                return self._make_response(REFUSAL_MESSAGES["empty"], input_tokens, 50)
            return self._make_response(REFUSAL_MESSAGES["missing_info"], input_tokens, 80)

        # 8. Gibberish (chỉ ký tự lạ, không có từ tiếng Việt/Anh)
        if self._is_gibberish(msg):
            return self._make_response(REFUSAL_MESSAGES["gibberish"], input_tokens, 60)

        # 9. Random infrastructure error (5%)
        if random.random() < RANDOM_ERROR_RATE:
            error_class, error_msg = random.choice([
                (TimeoutError,    "LLM inference timeout after 30s"),
                (ValueError,      "Context window exceeded: prompt too long"),
                (RuntimeError,    "LLM backend returned empty response"),
                (ConnectionError, "Model API connection refused"),
            ])
            raise error_class(error_msg)

        # ── Normal answer ──────────────────────────────────────
        answer = self._gen_answer(feature, msg, prompt)
        return self._make_response(answer, input_tokens, output_tokens)

    # ── Private helpers ────────────────────────────────────────

    def _make_response(self, text: str, tin: int, tout: int) -> FakeResponse:
        return FakeResponse(text=text, usage=FakeUsage(tin, tout), model=self.model)

    def _extract_message(self, prompt: str) -> str:
        match = re.search(r"Question=(.+?)$", prompt, re.DOTALL)
        return match.group(1).strip() if match else prompt[-200:]

    def _detect_feature(self, prompt: str) -> str:
        lower = prompt.lower()
        for feat in ["solve_exercise", "explain_concept", "generate_quiz", "grade_essay", "summary"]:
            if f"feature={feat}" in lower:
                return feat
        return "qa"

    def _match_any(self, text: str, patterns: list[str]) -> bool:
        lower = text.lower()
        return any(re.search(p, lower) for p in patterns)

    def _is_gibberish(self, text: str) -> bool:
        """Phát hiện chuỗi ký tự vô nghĩa (không có từ dài hơn 2 ký tự có nghĩa)."""
        words = re.findall(r"[a-zA-ZÀ-ỹ]{3,}", text)
        return len(words) == 0 and len(text.strip()) > 0

    def _strip_injection(self, msg: str) -> str:
        """Lấy phần câu hỏi thật sau từ khóa injection."""
        parts = re.split(r"[.!]\s+", msg)
        return " ".join(p for p in parts if not self._match_any(p, PROMPT_INJECTION_PATTERNS)).strip()

    def _extract_real_question(self, msg: str) -> str:
        """Lấy phần câu hỏi học thuật từ message có chứa thông tin nhạy cảm."""
        sentences = re.split(r"[.。]\s+", msg)
        academic = [s for s in sentences if any(kw in s.lower() for kw in
                    ["giải", "tính", "phương trình", "giải thích", "là gì", "bao nhiêu"])]
        return " ".join(academic).strip() or "câu hỏi của bạn"

    def _gen_answer(self, feature: str, msg: str, full_prompt: str) -> str:
        templates = ANSWER_TEMPLATES.get(feature, ANSWER_TEMPLATES["qa"])
        template  = random.choice(templates)
        return template.format(
            result=self._infer_result(msg),
            answer="Kiến thức tham khảo đã được truy xuất từ sách giáo khoa.",
            context="Tài liệu đã được truy xuất thành công.",
        )

    def _infer_result(self, msg: str) -> str:
        """Sinh kết quả phù hợp dựa trên nội dung câu hỏi."""
        lower = msg.lower()
        if "x² - 5x + 6" in lower or "x^2 - 5x + 6" in lower:
            return "x₁ = 2, x₂ = 3"
        if "2x + y = 5" in lower:
            return "x = 2, y = 1"
        if "3x - 7 = 11" in lower or "3x-7=11" in lower:
            return "x = 6"
        if "x + 5 = 10" in lower:
            return "x = 5"
        if "2x - 3 > 5" in lower:
            return "x > 4"
        if "x + 1 = 2" in lower:
            return "x = 1"
        if "hình tròn" in lower and ("5cm" in lower or "r = 5" in lower or "bán kính 5" in lower):
            return "S = 25π ≈ 78.54 cm²"
        if "120km" in lower and "2 giờ" in lower:
            return "v = 60 km/h"
        if "5kg" in lower and "20n" in lower.replace(" ", ""):
            return "a = F/m = 20/5 = 4 m/s²"
        if "5kg" in lower and "10 m/s" in lower:
            return "Eđ = ½×5×10² = 250 J"
        if "11,2 lít" in lower and "o2" in lower:
            return "n = 11.2/22.4 = 0.5 mol"
        if "x³ - 4x + 1" in lower or "x^3 - 4x + 1" in lower:
            return "y' = 3x² - 4"
        if "3 lần đều ra mặt ngửa" in lower:
            return "P = (1/2)³ = 1/8 = 0.125"
        return random.choice(["x = 2", "x = -3", "F = 6N", "v = 60 km/h", "n = 0.5 mol"])
