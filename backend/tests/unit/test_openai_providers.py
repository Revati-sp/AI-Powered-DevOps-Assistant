from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from app.core.config import get_settings
from app.core.exceptions import LLMProviderError, ValidationAppError
from app.services.llm.factory import SUPPORTED_PROVIDERS, get_llm_provider
from app.services.llm.llama import LlamaProvider
from app.services.llm.mistral import MistralProvider
from app.services.llm.url_validation import chat_completions_url, validate_llm_base_url


@pytest.fixture(autouse=True)
def _clear_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(
        host: str, *args: object, **kwargs: object
    ) -> list[tuple[int, int, int, str, tuple[str, int]]]:
        if host.endswith(".test") or host in {
            "api.example.com",
            "example.com",
            "api.llama.com",
            "api.mistral.ai",
        }:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        return real_getaddrinfo(host, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        "app.services.llm.url_validation.socket.getaddrinfo", fake_getaddrinfo
    )
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("provider_cls", "base", "model", "key"),
    [
        (LlamaProvider, "https://llama.test/v1", "llama-test", "llama-secret"),
        (MistralProvider, "https://mistral.test/v1", "mistral-test", "mistral-secret"),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_successful_generation(
    provider_cls: type,
    base: str,
    model: str,
    key: str,
) -> None:
    route = respx.post(f"{base}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "  Hello DevOps  "}}
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        provider = provider_cls(api_key=key, base_url=base, model=model, client=client)
        text = await provider.generate("ping", system_prompt="sys")
    assert text == "Hello DevOps"
    assert route.called
    request = route.calls.last.request
    assert request.url == f"{base}/chat/completions"
    body = request.read()
    assert model.encode() in body
    assert b"sys" in body
    assert b"ping" in body
    assert request.headers["Authorization"] == f"Bearer {key}"
    assert key not in str(text)


@pytest.mark.asyncio
@respx.mock
async def test_streaming_tokens() -> None:
    chunks = [
        b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
        b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
        b"data: [DONE]\n\n",
    ]

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"".join(chunks))

    respx.post("https://llama.test/v1/chat/completions").mock(side_effect=_handler)
    async with httpx.AsyncClient() as client:
        provider = LlamaProvider(
            api_key="k",
            base_url="https://llama.test/v1",
            model="m",
            client=client,
        )
        collected: list[str] = []
        async for part in provider.stream("q"):
            collected.append(part)
    assert collected == ["Hello", " world"]


@pytest.mark.asyncio
async def test_missing_api_key() -> None:
    with pytest.raises(LLMProviderError) as exc:
        LlamaProvider(api_key="", base_url="https://llama.test/v1", model="m")
    assert "LLAMA_API_KEY" in exc.value.message
    assert "secret" not in exc.value.message.lower() or "API" in exc.value.message


@pytest.mark.asyncio
@respx.mock
async def test_timeout_and_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    respx.post("https://llama.test/v1/chat/completions").mock(
        side_effect=httpx.TimeoutException("timeout")
    )
    async with httpx.AsyncClient() as client:
        provider = LlamaProvider(
            api_key="k",
            base_url="https://llama.test/v1",
            model="m",
            client=client,
            max_retries=2,
        )
        with pytest.raises(LLMProviderError, match="timed out"):
            await provider.generate("x")


@pytest.mark.asyncio
@respx.mock
async def test_connection_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    respx.post("https://mistral.test/v1/chat/completions").mock(
        side_effect=httpx.ConnectError("boom")
    )
    async with httpx.AsyncClient() as client:
        provider = MistralProvider(
            api_key="k",
            base_url="https://mistral.test/v1",
            model="m",
            client=client,
            max_retries=2,
        )
        with pytest.raises(LLMProviderError, match="connection failed"):
            await provider.generate("x")


@pytest.mark.asyncio
@respx.mock
async def test_http_401_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)
    route = respx.post("https://llama.test/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": "nope"})
    )
    async with httpx.AsyncClient() as client:
        provider = LlamaProvider(
            api_key="k",
            base_url="https://llama.test/v1",
            model="m",
            client=client,
            max_retries=3,
        )
        with pytest.raises(LLMProviderError, match="rejected"):
            await provider.generate("x")
    assert route.call_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
@respx.mock
async def test_http_429_and_500_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    route = respx.post("https://llama.test/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(429, json={"error": "slow"}),
            httpx.Response(500, json={"error": "err"}),
            httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            ),
        ]
    )
    async with httpx.AsyncClient() as client:
        provider = LlamaProvider(
            api_key="k",
            base_url="https://llama.test/v1",
            model="m",
            client=client,
            max_retries=3,
        )
        text = await provider.generate("x")
    assert text == "ok"
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_http_400_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)
    route = respx.post("https://mistral.test/v1/chat/completions").mock(
        return_value=httpx.Response(400, json={"error": "bad"})
    )
    async with httpx.AsyncClient() as client:
        provider = MistralProvider(
            api_key="k",
            base_url="https://mistral.test/v1",
            model="m",
            client=client,
            max_retries=3,
        )
        with pytest.raises(LLMProviderError, match="rejected"):
            await provider.generate("x")
    assert route.call_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
@respx.mock
async def test_malformed_and_missing_content() -> None:
    respx.post("https://llama.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, text="not-json")
    )
    async with httpx.AsyncClient() as client:
        provider = LlamaProvider(
            api_key="k",
            base_url="https://llama.test/v1",
            model="m",
            client=client,
        )
        with pytest.raises(LLMProviderError, match="malformed JSON"):
            await provider.generate("x")

    respx.post("https://llama.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {}}]})
    )
    async with httpx.AsyncClient() as client:
        provider = LlamaProvider(
            api_key="k",
            base_url="https://llama.test/v1",
            model="m",
            client=client,
        )
        with pytest.raises(LLMProviderError, match="no assistant content"):
            await provider.generate("x")


def test_factory_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("LLAMA_API_KEY", "l")
    monkeypatch.setenv("MISTRAL_API_KEY", "m")
    get_settings.cache_clear()
    assert get_llm_provider("GEMINI").name == "gemini"
    assert get_llm_provider("llama").name == "llama"
    assert get_llm_provider("Mistral").name == "mistral"
    assert SUPPORTED_PROVIDERS == {"gemini", "llama", "mistral"}
    with pytest.raises(ValidationAppError):
        get_llm_provider("claude")


def test_url_validation_and_join(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_INSECURE_LLM_HTTP", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError):
        validate_llm_base_url("http://example.com/v1", provider="llama")
    with pytest.raises(ValidationAppError):
        validate_llm_base_url("https://user:pass@example.com/v1", provider="llama")
    assert (
        chat_completions_url("https://example.com/v1/")
        == "https://example.com/v1/chat/completions"
    )
    assert (
        chat_completions_url("https://example.com/v1/chat/completions")
        == "https://example.com/v1/chat/completions"
    )
