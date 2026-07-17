from typing import Any, cast

from fastapi import APIRouter
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.schemas.common import APIResponse

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
