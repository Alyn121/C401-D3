from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import get_history, push_history, record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import tracing_enabled, rehydrate_from_logs

configure_logging()
log = get_logger()
app = FastAPI(
    title="AI Gia Sư — Observability Lab",
    description="Day 13 Lab: Monitoring, Logging & Tracing for AI Tutoring System",
    version="1.0.0",
)

# CORS — allow dashboard HTML to poll the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()

# Mount thư mục static để phục vụ Dashboard HTML
import pathlib
_static_dir = pathlib.Path(__file__).parent.parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
async def index() -> RedirectResponse:
    # Điều hướng trang chủ về Dashboard mặc định
    return RedirectResponse(url="/static/dashboard.html")


# ── Background task: push metrics history every 15s ───────────
async def _history_task() -> None:
    while True:
        await asyncio.sleep(15)
        push_history()


@app.on_event("startup")
async def startup() -> None:
    # Tự động nạp lại metrics từ file log cũ
    rehydrate_from_logs()
    # Khởi động task đẩy history metrics
    asyncio.create_task(_history_task())
    
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "ai-gia-su-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled(), "domain": "ai_tutor"},
    )


# ── Health & Metrics ──────────────────────────────────────────
@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.get("/metrics/history")
async def metrics_history() -> list:
    return get_history()


# ── Chat endpoint ─────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    from .incidents import STATE
    if STATE.get("api_rate_limit"):
        record_error("RateLimitError")
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    # 1. Ràng buộc các thông tin ngữ cảnh vào log tự động
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        subject=body.subject,
        grade=body.grade,
        env=os.getenv("APP_ENV", "dev"),
    )
    
    log.info(
        "request_received",
        service="api",
        payload={
            "message_preview": summarize_text(body.message),
            "subject": body.subject,
            "grade": body.grade,
        },
    )

    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
            subject=body.subject,
            grade=body.grade,
        )

        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            subject=body.subject,
            grade=body.grade,
            payload={
                "answer_preview": summarize_text(result.answer),
                "quality_score": getattr(result, 'quality_score', 0.0),
            },
        )

        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=getattr(result, 'quality_score', 0.0),
        )

    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


# ── Incident controls ─────────────────────────────────────────
@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
