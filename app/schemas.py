from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., examples=["u_student_01"])
    session_id: str = Field(..., examples=["s_math_01"])
    feature: str = Field(
        default="qa",
        examples=["qa", "summary", "solve_exercise", "explain_concept", "generate_quiz", "grade_essay"],
    )
    message: str = Field(..., min_length=1)
    # AI Tutor domain fields (optional — enriched from message or client)
    subject: str | None = Field(
        default=None,
        examples=["math", "literature", "physics", "chemistry", "english", "history"],
    )
    grade: str | None = Field(
        default=None,
        examples=["10", "11", "12", "university"],
    )


class ChatResponse(BaseModel):
    answer: str
    correlation_id: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LogRecord(BaseModel):
    # ── TẦNG 1: BẮT BUỘC ──────────────────────────────────────
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["info", "warning", "error", "critical"]
    service: str
    event: str
    correlation_id: str

    # ── TẦNG 2: CONTEXT ────────────────────────────────────────
    env: str | None = None
    user_id_hash: str | None = None
    session_id: str | None = None

    # ── TẦNG 2 MỞ RỘNG: AI Tutor Domain ───────────────────────
    feature: str | None = None      # solve_exercise | explain_concept | ...
    subject: str | None = None      # math | literature | physics | ...
    grade: str | None = None        # "10" | "11" | "12" | "university"

    # ── TẦNG 3: METRICS ────────────────────────────────────────
    model: str | None = None
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None

    # ── TẦNG 3 MỞ RỘNG: Quality ────────────────────────────────
    quality_score: float | None = None   # 0.0 → 1.0 (heuristic)
    steps_count: int | None = None       # số bước giải (với solve_exercise)

    # ── TẦNG 4: LỖI & CÔNG CỤ ─────────────────────────────────
    error_type: str | None = None
    tool_name: str | None = None

    # ── TẦNG 5: CHI TIẾT TỰ DO ────────────────────────────────
    payload: dict[str, Any] | None = None
