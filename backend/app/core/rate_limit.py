from __future__ import annotations

import enum
import time
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Sliding-window rate limiter using a Redis sorted set + Lua for atomicity.
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count < limit then
  redis.call('ZADD', key, now, member)
  redis.call('EXPIRE', key, math.ceil(window / 1000) + 1)
  local remaining = limit - count - 1
  local reset_ms = window
  return {1, remaining, reset_ms, limit}
end

local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
local retry_after_ms = window
if oldest[2] then
  retry_after_ms = math.max(1, (tonumber(oldest[2]) + window) - now)
end
return {0, 0, retry_after_ms, limit}
"""


class RateLimitCategory(str, enum.Enum):
    AUTH = "auth"
    API = "api"
    LLM = "llm"
    STREAM = "stream"
    UPLOAD = "upload"


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    reset_seconds: int


class RateLimiter:
    def __init__(
        self,
        redis_client: Redis | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._redis = redis_client
        self._owns_redis = redis_client is None
        self._script: Any | None = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = redis_from_url(
                self.settings.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    def limit_for(self, category: RateLimitCategory) -> int:
        mapping = {
            RateLimitCategory.AUTH: self.settings.rate_limit_auth_per_minute,
            RateLimitCategory.API: self.settings.rate_limit_api_per_minute,
            RateLimitCategory.LLM: self.settings.rate_limit_llm_per_minute,
            RateLimitCategory.STREAM: self.settings.rate_limit_stream_per_minute,
            RateLimitCategory.UPLOAD: self.settings.rate_limit_upload_per_minute,
        }
        return mapping[category]

    def _key(self, category: RateLimitCategory, identity: str) -> str:
        return f"{self.settings.rate_limit_redis_prefix}:{category.value}:{identity}"

    async def check(
        self,
        category: RateLimitCategory,
        identity: str,
        *,
        now_ms: int | None = None,
    ) -> RateLimitResult:
        if not self.settings.rate_limit_enabled:
            limit = self.limit_for(category)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                retry_after_seconds=0,
                reset_seconds=60,
            )

        limit = self.limit_for(category)
        window_ms = 60_000
        current_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        member = f"{current_ms}-{identity}"

        try:
            client = await self._get_redis()
            if self._script is None:
                self._script = client.register_script(SLIDING_WINDOW_LUA)
            result = await self._script(
                keys=[self._key(category, identity)],
                args=[current_ms, window_ms, limit, member],
            )
            allowed = bool(int(result[0]))
            remaining = int(result[1])
            retry_or_reset_ms = int(result[2])
            configured_limit = int(result[3])
            retry_after = max(1, (retry_or_reset_ms + 999) // 1000)
            reset_seconds = max(1, (retry_or_reset_ms + 999) // 1000)
            return RateLimitResult(
                allowed=allowed,
                limit=configured_limit,
                remaining=max(0, remaining),
                retry_after_seconds=0 if allowed else retry_after,
                reset_seconds=reset_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Rate limiter Redis unavailable",
                extra={
                    "category": category.value,
                    "fail_open": self.settings.rate_limit_fail_open,
                },
            )
            if self.settings.rate_limit_fail_open:
                return RateLimitResult(
                    allowed=True,
                    limit=limit,
                    remaining=limit,
                    retry_after_seconds=0,
                    reset_seconds=60,
                )
            raise AppError(
                "Rate limiting temporarily unavailable.",
                code="RATE_LIMIT_UNAVAILABLE",
                status_code=503,
                details={"category": category.value},
            ) from exc

    async def enforce(
        self,
        category: RateLimitCategory,
        identity: str,
        *,
        now_ms: int | None = None,
    ) -> RateLimitResult:
        result = await self.check(category, identity, now_ms=now_ms)
        if not result.allowed:
            raise RateLimitError(
                "Too many requests. Try again later.",
                code="RATE_LIMIT_EXCEEDED",
                details={
                    "retry_after_seconds": result.retry_after_seconds,
                    "limit": result.limit,
                    "remaining": result.remaining,
                    "reset_seconds": result.reset_seconds,
                    "category": category.value,
                },
            )
        return result

    async def aclose(self) -> None:
        if self._owns_redis and self._redis is not None:
            await self._redis.aclose()


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter | None) -> None:
    global _rate_limiter
    _rate_limiter = limiter
