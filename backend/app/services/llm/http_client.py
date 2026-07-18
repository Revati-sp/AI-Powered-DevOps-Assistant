from __future__ import annotations

import httpx

from app.core.config import get_settings


def create_llm_http_client(*, timeout_seconds: int | None = None) -> httpx.AsyncClient:
    """Shared outbound LLM HTTP client with conservative defaults."""
    settings = get_settings()
    timeout = timeout_seconds or settings.effective_llm_timeout
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        follow_redirects=False,
    )
