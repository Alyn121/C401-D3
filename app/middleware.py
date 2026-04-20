from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

# Max N requests per session_id trong cửa sổ thời gian T giây
RATE_LIMIT_MAX    = 2000    # tối đa 2000 requests (đã nâng cấp để test tải)
RATE_LIMIT_WINDOW = 60      # trong 60 giây
_rate_buckets: dict[str, deque] = defaultdict(deque)

# ── Request size guard ─────────────────────────────────────────
MAX_CONTENT_LENGTH = 32 * 1024   # 32KB — chống payload quá lớn


def _is_rate_limited(session_id: str) -> bool:
    """Sliding window rate limiter theo session_id."""
    now    = time.monotonic()
    bucket = _rate_buckets[session_id]

    # Xóa các timestamp đã cũ hơn cửa sổ thời gian
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_MAX:
        return True

    bucket.append(now)
    return False


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # ── 1. Clear contextvars để tránh rò rỉ giữa các requests ──
        clear_contextvars()

        # ── 2. Tạo / lấy Correlation ID ───────────────────────────
        incoming = request.headers.get("x-request-id")
        correlation_id = incoming if incoming else f"req-{uuid.uuid4().hex[:8]}"
        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        # ── 3. Content-Length guard (chỉ áp dụng cho POST) ────────
        if request.method == "POST":
            content_length = int(request.headers.get("content-length", 0))
            if content_length > MAX_CONTENT_LENGTH:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "PayloadTooLarge",
                        "detail": f"Request body exceeds {MAX_CONTENT_LENGTH // 1024}KB limit.",
                        "correlation_id": correlation_id,
                    },
                    headers={"x-request-id": correlation_id},
                )

        # ── 4. Rate Limiting theo session_id ──────────────────────
        # Chỉ áp dụng cho /chat để không block /health, /metrics
        if request.url.path == "/chat":
            # Lấy session_id từ query params hoặc sẽ check sau khi parse body
            # Dùng client IP làm fallback key nếu không có session
            client_ip  = (request.client.host if request.client else "unknown")
            rate_key   = request.headers.get("x-session-id", client_ip)

            if _is_rate_limited(rate_key):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "RateLimitError",
                        "detail": f"Too many requests: max {RATE_LIMIT_MAX} per {RATE_LIMIT_WINDOW}s.",
                        "correlation_id": correlation_id,
                    },
                    headers={
                        "x-request-id":      correlation_id,
                        "retry-after":       str(RATE_LIMIT_WINDOW),
                        "x-rate-limit-max":  str(RATE_LIMIT_MAX),
                    },
                )

        # ── 5. Xử lý request thật sự ──────────────────────────────
        start    = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # ── 6. Gắn headers vào response ───────────────────────────
        response.headers["x-request-id"]       = correlation_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)
        response.headers["x-rate-limit-max"]   = str(RATE_LIMIT_MAX)
        response.headers["x-rate-limit-window"] = f"{RATE_LIMIT_WINDOW}s"

        return response
