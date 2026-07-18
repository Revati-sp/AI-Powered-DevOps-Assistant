from __future__ import annotations

import os
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-123456789012345678")
os.environ.setdefault("REFRESH_TOKEN_PEPPER", "test-refresh-pepper-123456789012")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("LLAMA_API_KEY", "test-llama-key")
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-key")
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("ALLOWED_ORIGINS", "http://testserver")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ALLOW_INSECURE_LLM_HTTP", "true")
os.environ.setdefault("SSE_HEARTBEAT_INTERVAL_SECONDS", "0.05")
os.environ.setdefault("LLM_MAX_RETRIES", "3")

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.rate_limit import set_rate_limiter
from app.main import app
from app.services.llm.base import LLMProvider, chunk_text

get_settings.cache_clear()
set_rate_limiter(None)


class FakeLLMProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self,
        response: str = "Suggested steps for CrashLoopBackOff triage.",
        *,
        provider_name: str = "gemini",
        fail: bool = False,
        stream_chunks: list[str] | None = None,
    ) -> None:
        self.response = response
        self.name = provider_name
        self.fail = fail
        self.stream_chunks = stream_chunks
        self.calls: list[dict[str, Any]] = []
        self.stream_calls = 0

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        if self.fail:
            from app.core.exceptions import LLMProviderError

            raise LLMProviderError(
                "LLM provider request failed.",
                details={"provider": self.name},
            )
        return self.response

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        self.stream_calls += 1
        await self.generate(
            prompt,
            system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        chunks = self.stream_chunks or chunk_text(self.response)
        for chunk in chunks:
            yield chunk


@pytest.fixture
def fake_llm() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, fake_llm: FakeLLMProvider, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
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
        "app.services.chat_service.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )
    monkeypatch.setattr(
        "app.services.log_analyzer.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )
    monkeypatch.setattr(
        "app.services.docker_generator.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )
    monkeypatch.setattr(
        "app.services.shell_command_service.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )
    monkeypatch.setattr(
        "app.services.security_review_service.get_llm_provider",
        lambda provider_name=None: fake_llm,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
    set_rate_limiter(None)


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dev@example.com",
            "username": "devops",
            "password": "DevOpsPass123!",
        },
    )
    assert register.status_code == 200, register.text

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "devops", "password": "DevOpsPass123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
