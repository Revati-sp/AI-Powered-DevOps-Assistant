from __future__ import annotations

import json
from uuid import UUID, uuid4

import pytest
from app.models.message import Message, MessageRole
from app.utils.sse import encode_sse
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import FakeLLMProvider


def _parse_sse(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    blocks = [block for block in body.split("\n\n") if block.strip()]
    for block in blocks:
        event_name = ""
        data_line = ""
        for line in block.split("\n"):
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_line = line.split(":", 1)[1].strip()
        assert event_name
        events.append((event_name, json.loads(data_line)))
    return events


def test_encode_sse_format() -> None:
    encoded = encode_sse("token", {"content": "hi"})
    assert encoded.startswith("event: token\n")
    assert 'data: {"content":"hi"}' in encoded
    assert encoded.endswith("\n\n")


@pytest.mark.asyncio
async def test_stream_new_conversation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    fake_llm: FakeLLMProvider,
    db_session: AsyncSession,
) -> None:
    fake_llm.stream_chunks = ["The pod", " may be restarting"]
    response = await client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={
            "message": "Why is my Kubernetes pod restarting?",
            "conversation_id": None,
            "provider": "gemini",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = _parse_sse(response.text)
    assert events[0][0] == "conversation"
    assert "conversation_id" in events[0][1]
    assert events[-1][0] == "completed"
    assert any(name == "token" for name, _ in events)
    for name, data in events:
        if name == "token":
            assert isinstance(data["content"], str)

    conversation_id = UUID(str(events[0][1]["conversation_id"]))
    db_session.expire_all()
    result = await db_session.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    messages = list(result.scalars().all())
    roles = {m.role for m in messages}
    assert MessageRole.USER in roles
    assert MessageRole.ASSISTANT in roles


@pytest.mark.asyncio
async def test_stream_existing_conversation_and_providers(
    client: AsyncClient,
    auth_headers: dict[str, str],
    fake_llm: FakeLLMProvider,
) -> None:
    create = await client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "initial", "provider": "gemini"},
    )
    conversation_id = create.json()["data"]["conversation_id"]

    for provider_name in ("gemini", "llama", "mistral"):
        fake_llm.name = provider_name
        fake_llm.stream_chunks = ["ok"]
        response = await client.post(
            "/api/v1/chat/stream",
            headers=auth_headers,
            json={
                "message": f"follow up {provider_name}",
                "conversation_id": conversation_id,
                "provider": provider_name,
            },
        )
        assert response.status_code == 200
        events = _parse_sse(response.text)
        assert events[0][0] == "conversation"
        assert events[-1][0] == "completed"
        assert events[-1][1]["provider"] == provider_name


@pytest.mark.asyncio
async def test_stream_fallback_chunks(
    client: AsyncClient,
    auth_headers: dict[str, str],
    fake_llm: FakeLLMProvider,
) -> None:
    fake_llm.stream_chunks = None
    fake_llm.response = "Word aware chunked fallback response text"
    response = await client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={"message": "fallback please", "provider": "gemini"},
    )
    events = _parse_sse(response.text)
    tokens = [data["content"] for name, data in events if name == "token"]
    assert tokens
    assert all(isinstance(t, str) and t for t in tokens)


@pytest.mark.asyncio
async def test_stream_failure_does_not_persist_assistant(
    client: AsyncClient,
    auth_headers: dict[str, str],
    fake_llm: FakeLLMProvider,
    db_session: AsyncSession,
) -> None:
    fake_llm.fail = True
    response = await client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={"message": "will fail", "provider": "gemini"},
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert events[0][0] == "conversation"
    assert any(name == "error" for name, _ in events)
    assert all(name != "completed" for name, _ in events)
    conversation_id = UUID(str(events[0][1]["conversation_id"]))
    db_session.expire_all()
    result = await db_session.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    messages = list(result.scalars().all())
    assert len(messages) == 1
    assert messages[0].role == MessageRole.USER


@pytest.mark.asyncio
async def test_stream_invalid_provider_and_missing_conversation(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    bad = await client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={"message": "hi", "provider": "claude"},
    )
    assert bad.status_code == 422

    missing = await client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={
            "message": "hi",
            "conversation_id": str(uuid4()),
            "provider": "gemini",
        },
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_stream_cross_user_forbidden(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "mine", "provider": "gemini"},
    )
    conversation_id = created.json()["data"]["conversation_id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "otheruser",
            "password": "DevOpsPass123!",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "otheruser", "password": "DevOpsPass123!"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = await client.post(
        "/api/v1/chat/stream",
        headers=other_headers,
        json={
            "message": "steal",
            "conversation_id": conversation_id,
            "provider": "gemini",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stream_heartbeat(
    client: AsyncClient,
    auth_headers: dict[str, str],
    fake_llm: FakeLLMProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asyncio

    async def slow_stream(*_args, **_kwargs):
        await asyncio.sleep(0.12)
        yield "late"

    monkeypatch.setattr(fake_llm, "stream", slow_stream)
    response = await client.post(
        "/api/v1/chat/stream",
        headers=auth_headers,
        json={"message": "heartbeat", "provider": "gemini"},
    )
    events = _parse_sse(response.text)
    assert any(name == "heartbeat" for name, _ in events)
