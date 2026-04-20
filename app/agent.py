from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .logging_config import get_logger
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import langfuse_context, observe

log = get_logger()


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float
    steps_count: int


class LabAgent:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe()
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        subject: str | None = None,
        grade: str | None = None,
    ) -> AgentResult:
        started = time.perf_counter()

        # ── RAG Retrieval Step ──────────────────────────────────
        rag_start = time.perf_counter()
        docs = retrieve(message)
        rag_latency_ms = int((time.perf_counter() - rag_start) * 1000)

        log.info(
            "retrieval_step",
            service="rag",
            tool_name="curriculum_retriever",
            latency_ms=rag_latency_ms,
            payload={
                "doc_count": len(docs),
                "top_k": 10,
                "source": f"sgk_{subject or 'general'}",
                "query_preview": summarize_text(message),
                "subject": subject,
                "grade": grade,
            },
        )

        # ── LLM Inference Step ──────────────────────────────────
        prompt = f"Feature={feature}\nSubject={subject}\nGrade={grade}\nDocs={docs}\nQuestion={message}"
        llm_start = time.perf_counter()
        response = self.llm.generate(prompt)
        llm_latency_ms = int((time.perf_counter() - llm_start) * 1000)

        log.info(
            "inference_step",
            service="llm",
            model=self.model,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens),
            latency_ms=llm_latency_ms,
            payload={
                "feature": feature,
                "subject": subject,
                "step_by_step": feature == "solve_exercise",
                "hint_mode": False,
            },
        )

        quality_score = self._heuristic_quality(message, response.text, docs, feature)
        steps_count = self._count_steps(response.text)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        # ── Langfuse Tracing ────────────────────────────────────
        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model, subject or "general", grade or "unknown"],
        )
        langfuse_context.update_current_observation(
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "subject": subject,
                "grade": grade,
                "steps_count": steps_count,
            },
            usage_details={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
        )

        # ── Record Metrics ──────────────────────────────────────
        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
            steps_count=steps_count,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        # Gemini 2.0 Flash pricing (approximate)
        input_cost = (tokens_in / 1_000_000) * 0.075
        output_cost = (tokens_out / 1_000_000) * 0.30
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str], feature: str) -> float:
        score = 0.5
        if docs and "Không tìm thấy" not in docs[0]:
            score += 0.2
        if len(answer) > 100:
            score += 0.1
        q_words = question.lower().split()[:3]
        if q_words and any(token in answer.lower() for token in q_words):
            score += 0.1
        if feature == "solve_exercise" and ("bước" in answer.lower() or "step" in answer.lower()):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)

    def _count_steps(self, answer: str) -> int:
        """Count numbered steps in the answer for pedagogical metrics."""
        import re
        steps = re.findall(r"(?:bước\s*\d+|step\s*\d+|\d+\.\s)", answer.lower())
        return len(steps)
