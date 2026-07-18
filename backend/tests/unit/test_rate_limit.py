from __future__ import annotations

import asyncio

import fakeredis.aioredis
import pytest
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AppError, RateLimitError
from app.core.rate_limit import (
    RateLimitCategory,
    RateLimiter,
    get_rate_limiter,
    set_rate_limiter,
)
from app.main import app
from app.utils.client_ip import resolve_client_ip
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import FakeLLMProvider


@pytest.fixture
async def fake_redis() -> fakeredis.aioredis.FakeRedis:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def limiter(fake_redis: fakeredis.aioredis.FakeRedis, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_MINUTE", "2")
    monkeypatch.setenv("RATE_LIMIT_API_PER_MINUTE", "3")
    monkeypatch.setenv("RATE_LIMIT_LLM_PER_MINUTE", "2")
    monkeypatch.setenv("RATE_LIMIT_STREAM_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_UPLOAD_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_FAIL_OPEN", "true")
    get_settings.cache_clear()
    settings = get_settings()
    instance = RateLimiter(redis_client=fake_redis, settings=settings)
    set_rate_limiter(instance)
    yield instance
    set_rate_limiter(None)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sliding_window_and_headers(limiter: RateLimiter) -> None:
    now = 1_000_000
    first = await limiter.enforce(RateLimitCategory.AUTH, "ip:1.1.1.1", now_ms=now)
    assert first.allowed is True
    second = await limiter.enforce(RateLimitCategory.AUTH, "ip:1.1.1.1", now_ms=now + 1)
    assert second.remaining == 0
    with pytest.raises(RateLimitError) as exc:
        await limiter.enforce(RateLimitCategory.AUTH, "ip:1.1.1.1", now_ms=now + 2)
    assert exc.value.code == "RATE_LIMIT_EXCEEDED"
    assert "retry_after_seconds" in exc.value.details

    # Independent identities.
    other = await limiter.enforce(RateLimitCategory.AUTH, "ip:2.2.2.2", now_ms=now)
    assert other.allowed is True

    # Shared across "instances" using same Redis.
    twin = RateLimiter(redis_client=limiter._redis, settings=limiter.settings)
    with pytest.raises(RateLimitError):
        await twin.enforce(RateLimitCategory.AUTH, "ip:1.1.1.1", now_ms=now + 3)


@pytest.mark.asyncio
async def test_disabled_and_fail_modes(
    fake_redis: fakeredis.aioredis.FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
    disabled = RateLimiter(redis_client=fake_redis, settings=get_settings())
    for i in range(20):
        result = await disabled.enforce(RateLimitCategory.API, "user:x", now_ms=i)
        assert result.allowed is True

    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_FAIL_OPEN", "true")
    get_settings.cache_clear()

    class BrokenRedis:
        async def register_script(self, *_args, **_kwargs):
            raise RuntimeError("redis down")

    open_limiter = RateLimiter(redis_client=BrokenRedis(), settings=get_settings())  # type: ignore[arg-type]
    allowed = await open_limiter.check(RateLimitCategory.API, "user:x")
    assert allowed.allowed is True

    monkeypatch.setenv("RATE_LIMIT_FAIL_OPEN", "false")
    get_settings.cache_clear()
    closed = RateLimiter(redis_client=BrokenRedis(), settings=get_settings())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await closed.enforce(RateLimitCategory.API, "user:x")
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_atomic_concurrent_requests(limiter: RateLimiter) -> None:
    now = 5_000_000

    async def hit(i: int) -> bool:
        try:
            await limiter.enforce(
                RateLimitCategory.LLM, "user:concurrent", now_ms=now + i
            )
            return True
        except RateLimitError:
            return False

    results = await asyncio.gather(*[hit(i) for i in range(10)])
    assert sum(results) == 2


def test_client_ip_ignores_forwarded_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "0")
    get_settings.cache_clear()
    request = MagicMock()
    request.client.host = "10.0.0.5"
    request.headers = {"x-forwarded-for": "8.8.8.8, 1.1.1.1", "x-real-ip": "9.9.9.9"}
    assert resolve_client_ip(request) == "10.0.0.5"

    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "1")
    get_settings.cache_clear()
    assert resolve_client_ip(request) == "8.8.8.8"


def test_client_ip_trusts_forwarded_for_allowlisted_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "0")
    monkeypatch.setenv("TRUSTED_PROXY_IPS", "10.0.0.5")
    get_settings.cache_clear()
    request = MagicMock()
    request.client.host = "10.0.0.5"
    request.headers = {"x-forwarded-for": "203.0.113.10"}
    assert resolve_client_ip(request) == "203.0.113.10"


@pytest.mark.asyncio
async def test_http_rate_limits_and_stream_precheck(
    db_session: AsyncSession,
    fake_llm: FakeLLMProvider,
    limiter: RateLimiter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        "app.services.llm.factory.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )
    monkeypatch.setattr(
        "app.services.provider_service.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Auth IP limit = 2
        r1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "username": "user_a",
                "password": "DevOpsPass123!",
            },
        )
        assert r1.status_code == 200
        r2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "b@example.com",
                "username": "user_b",
                "password": "DevOpsPass123!",
            },
        )
        assert r2.status_code == 200
        r3 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "c@example.com",
                "username": "user_c",
                "password": "DevOpsPass123!",
            },
        )
        assert r3.status_code == 429
        assert r3.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in r3.headers
        assert "X-RateLimit-Limit" in r3.headers

        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "user_a", "password": "DevOpsPass123!"},
        )
        # login may be rate-limited by same IP already at 2; create fresh identity via limiter reset
    # Re-open client with cleared redis keys for authenticated flows
    await limiter._redis.flushdb()  # type: ignore[union-attr]

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "stream@example.com",
                "username": "streamer",
                "password": "DevOpsPass123!",
            },
        )
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "streamer", "password": "DevOpsPass123!"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        health = await client.get("/health")
        assert health.status_code == 200

        first = await client.post(
            "/api/v1/chat/stream",
            headers=headers,
            json={"message": "one", "provider": "gemini"},
        )
        assert first.status_code == 200
        assert fake_llm.stream_calls == 1

        second = await client.post(
            "/api/v1/chat/stream",
            headers=headers,
            json={"message": "two", "provider": "gemini"},
        )
        assert second.status_code == 429
        assert fake_llm.stream_calls == 1
        assert second.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    app.dependency_overrides.clear()
    set_rate_limiter(None)


@pytest.mark.asyncio
async def test_get_rate_limiter_singleton(limiter: RateLimiter) -> None:
    assert get_rate_limiter() is limiter
