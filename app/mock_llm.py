from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .incidents import STATE

# ── Error simulation config ────────────────────────────────────
# Keywords trong message sẽ trigger lỗi tương ứng
ERROR_TRIGGERS: dict[str, type[Exception]] = {
    "crash":        RuntimeError,
    "timeout":      TimeoutError,
    "lỗi":          ValueError,
    "error":        ValueError,
    "hack":         PermissionError,
    "delete all":   PermissionError,
    "injection":    PermissionError,
    "overload":     MemoryError,
}

# Tỷ lệ lỗi ngẫu nhiên để dashboard luôn có error data (5%)
RANDOM_ERROR_RATE = 0.05

ANSWER_TEMPLATES: dict[str, list[str]] = {
    "solve_exercise": [
        "Bước 1: Xác định dạng bài và công thức cần áp dụng.\nBước 2: Thay số vào công thức.\nBước 3: Tính toán.\nBước 4: Kiểm tra đáp án.\nKết quả: {result}.",
        "Giải:\n1. Phân tích đề bài: Xác định ẩn và điều kiện.\n2. Lập phương trình/bất phương trình.\n3. Giải và tìm nghiệm.\n4. Kết luận: Vậy {result}.",
        "Áp dụng công thức đã học:\n- Bước 1: Tính delta = b² - 4ac\n- Bước 2: Xét dấu delta\n- Bước 3: Tính nghiệm\nĐáp số: {result}.",
    ],
    "explain_concept": [
        "Khái niệm được giải thích như sau:\n📖 Định nghĩa: Đây là một khái niệm quan trọng trong chương trình học.\n🔑 Tính chất chính:\n  • Tính chất 1: Áp dụng trong trường hợp...\n  • Tính chất 2: Liên quan đến...\n💡 Ví dụ minh họa: Cho bài toán cụ thể, ta thấy...",
        "Để hiểu rõ về chủ đề này:\n1️⃣ Khái niệm cơ bản: Định nghĩa và phạm vi áp dụng.\n2️⃣ Công thức/Quy tắc: Các công thức cần ghi nhớ.\n3️⃣ Ví dụ áp dụng: Bài tập mẫu.\n4️⃣ Lưu ý: Những điểm dễ nhầm lẫn.",
    ],
    "generate_quiz": [
        "📝 Bài tập luyện cho bạn:\n\nCâu 1 (Dễ - 2đ): Phát biểu định nghĩa và nêu 2 ví dụ.\nCâu 2 (Trung bình - 3đ): Tính giá trị của biểu thức cho trước.\nCâu 3 (Khó - 5đ): Chứng minh tính chất và áp dụng vào bài toán thực tế.\n\n⏱ Thời gian: 20 phút | Không sử dụng tài liệu.",
        "🎯 Bộ câu hỏi ôn tập:\n\n[TRẮC NGHIỆM]\n1. Khẳng định nào sau đây ĐÚNG?\n   A. ... B. ... C. ... D. ...\n\n[TỰ LUẬN]\n2. Giải bài toán sau và trình bày đầy đủ các bước.",
    ],
    "grade_essay": [
        "📊 Nhận xét bài làm:\n\n✅ Điểm mạnh:\n  • Bố cục rõ ràng, có mở - thân - kết đầy đủ\n  • Luận điểm chặt chẽ, có dẫn chứng\n\n⚠️ Điểm cần cải thiện:\n  • Cần thêm dẫn chứng cụ thể hơn\n  • Kết bài chưa súc tích\n\n📝 Điểm ước tính: 7.5/10\n💡 Gợi ý: Bổ sung trích dẫn từ tác phẩm gốc.",
    ],
    "qa": [
        "Dựa trên tài liệu tham khảo, câu trả lời là:\n{answer}\n\n📚 Nguồn: Sách giáo khoa và tài liệu tham khảo đã được truy xuất.\n💡 Lưu ý: Đây là kiến thức trọng tâm thường xuất hiện trong đề thi.",
        "Theo sách giáo khoa:\n{answer}\n\n🎯 Đây là nội dung quan trọng cần ghi nhớ. Bạn có muốn làm bài tập luyện về chủ đề này không?",
    ],
    "summary": [
        "📋 Tóm tắt nội dung chính:\n\n• Điểm 1: Khái niệm và định nghĩa cốt lõi\n• Điểm 2: Các công thức và quy tắc quan trọng\n• Điểm 3: Ứng dụng thực tế trong đời sống\n• Điểm 4: Những lưu ý cần ghi nhớ khi làm bài\n\n🔥 Đây là những kiến thức trọng tâm thường xuất hiện trong bài thi THPT Quốc gia.",
    ],
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
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(120, 280)
        if STATE["cost_spike"]:
            output_tokens *= 4

        # ── Keyword-based error triggers ───────────────────────
        prompt_lower = prompt.lower()
        for keyword, exc_class in ERROR_TRIGGERS.items():
            if keyword in prompt_lower:
                raise exc_class(
                    f"LLM refused to process: detected trigger keyword '{keyword}'"
                )

        # ── Random error (5% rate) to generate error metrics ──
        if random.random() < RANDOM_ERROR_RATE:
            error_class = random.choice([
                (TimeoutError,    "LLM inference timeout after 30s"),
                (ValueError,      "Invalid prompt format: context window exceeded"),
                (RuntimeError,    "LLM backend returned empty response"),
                (ConnectionError, "Model API connection refused"),
            ])
            raise error_class[0](error_class[1])

        # ── Normal response ────────────────────────────────────
        feature = self._detect_feature(prompt)
        templates = ANSWER_TEMPLATES.get(feature, ANSWER_TEMPLATES["qa"])
        template = random.choice(templates)

        answer = template.format(
            result=random.choice(["x = 2", "x = -3", "x₁=2, x₂=3", "F = 6N", "vô nghiệm"]),
            concept="khái niệm này",
            answer="Kiến thức liên quan đã được truy xuất từ sách giáo khoa.",
            context="Tài liệu tham khảo đã được tìm thấy.",
        )

        return FakeResponse(
            text=answer,
            usage=FakeUsage(input_tokens, output_tokens),
            model=self.model,
        )

    def _detect_feature(self, prompt: str) -> str:
        lower = prompt.lower()
        if "feature=solve_exercise"   in lower: return "solve_exercise"
        if "feature=explain_concept"  in lower: return "explain_concept"
        if "feature=generate_quiz"    in lower: return "generate_quiz"
        if "feature=grade_essay"      in lower: return "grade_essay"
        if "feature=summary"          in lower: return "summary"
        return "qa"
