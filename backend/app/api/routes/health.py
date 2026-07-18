from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import AppError, UnauthorizedError
from app.core.metrics import render_metrics
from app.core.security import decode_access_token
from app.schemas.common import APIResponse
from app.utils.client_ip import resolve_client_ip

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse[dict[str, str]])
async def health() -> APIResponse[dict[str, str]]:
    return APIResponse(success=True, data={"status": "ok"})


@router.get("/ready", response_model=APIResponse[dict[str, str]])
async def ready() -> APIResponse[dict[str, str]]:
    settings = get_settings()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise AppError(
            "Database is not ready",
            code="NOT_READY",
            status_code=503,
            details={"component": "database"},
        ) from exc

    try:
        client = cast(Any, redis_from_url(settings.redis_url))
        pong = await client.ping()
        await client.aclose()
        if not pong:
            raise RuntimeError("Redis ping failed")
    except Exception as exc:  # noqa: BLE001
        raise AppError(
            "Redis is not ready",
            code="NOT_READY",
            status_code=503,
            details={"component": "redis"},
        ) from exc

    return APIResponse(
        success=True,
        data={"status": "ready", "database": "ok", "redis": "ok"},
    )


async def _require_metrics_access(request: Request) -> None:
    settings = get_settings()
    if not settings.metrics_enabled:
        raise AppError("Metrics are disabled", code="NOT_FOUND", status_code=404)

    allowed_ips = settings.metrics_allowed_ip_list
    if allowed_ips and resolve_client_ip(request) not in allowed_ips:
        raise AppError("Metrics access denied", code="FORBIDDEN", status_code=403)

    if not settings.metrics_require_auth:
        return

    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise UnauthorizedError("Authentication required for metrics")
    token = auth_header.split(" ", 1)[1]
    decode_access_token(token)


@router.get("/metrics")
async def metrics(request: Request) -> Response:
    await _require_metrics_access(request)
    body, content_type = render_metrics()
    return PlainTextResponse(content=body.decode("utf-8"), media_type=content_type)
