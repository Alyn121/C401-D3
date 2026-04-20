from __future__ import annotations

import os
import functools
from typing import Any

# BẢN MOCK NÂNG CẤP: Chạy không cần thư viện Langfuse
def observe(*args: Any, **kwargs: Any):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            return func(*args, **kwargs)
        return wrapper
    return decorator

class _DummyContext:
    def update_current_trace(self, **kwargs: Any) -> None:
        # In log chuyên nghiệp để giám sát Metadata giáo dục
        tags = kwargs.get("tags", [])
        metadata = kwargs.get("metadata", {})
        print(f"📡 [TRACE] interaction | User: {kwargs.get('user_id')} | Subject: {metadata.get('subject') or 'unknown'}")
        return None

    def update_current_observation(self, **kwargs: Any) -> None:
        metadata = kwargs.get("metadata", {})
        print(f"🔍 [OBSERVATION] Docs: {metadata.get('doc_count')} | Snippet: {metadata.get('query_preview')}")
        return None

# Đối tượng giả lập dùng chung
langfuse_context = _DummyContext()

def tracing_enabled() -> bool:
    return True

def rehydrate_from_logs() -> None:
    """Giả lập việc nạp lại dữ liệu từ logs."""
    return None

def enrich_trace(
    user_id: str,
    session_id: str,
    feature: str,
    model: str,
    message: str,
    docs: list[str],
    usage: dict[str, int],
    subject: str | None = None,
    grade: str | None = None
) -> None:
    """Tiện ích nâng cấp để ghi log quan sát chuyên nghiệp dựa trên Schema cơ bản."""
    from .pii import hash_user_id, summarize_text
    
    # 1. Bảo mật và Định danh toàn bộ Trace
    langfuse_context.update_current_trace(
        user_id=hash_user_id(user_id),
        session_id=session_id,
        tags=["lab", feature, model, subject or "general"],
        metadata={
            "subject": subject,
            "grade": grade,
            "env": os.getenv("APP_ENV", "dev")
        }
    )
    
    # 2. Ghi lại chi tiết bước thực thi
    langfuse_context.update_current_observation(
        metadata={
            "doc_count": len(docs),
            "query_preview": summarize_text(message),
            "subject": subject
        },
        usage_details=usage
    )
