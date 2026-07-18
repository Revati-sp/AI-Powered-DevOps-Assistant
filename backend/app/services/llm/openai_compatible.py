from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider
from app.services.llm.http_client import create_llm_http_client
from app.services.llm.url_validation import chat_completions_url, validate_llm_base_url

logger = get_logger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS = {400, 401, 403, 404}


class OpenAICompatibleProvider(LLMProvider):
    """Shared OpenAI-compatible chat completions client (Llama, Mistral, etc.)."""

    name: str
    _api_key_env: str

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        provider_name: str,
        api_key_env: str,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        if not api_key:
            raise LLMProviderError(
                f"{api_key_env} is not configured.",
                details={"provider": provider_name},
            )

        self.name = provider_name
        self._api_key_env = api_key_env
        self.api_key = api_key
        self.base_url = validate_llm_base_url(base_url, provider=provider_name)
        self.model = model
        self.timeout_seconds = timeout_seconds or settings.effective_llm_timeout
        self.max_retries = (
            max_retries if max_retries is not None else settings.llm_max_retries
        )
        self._owns_client = client is None
        self._client = client or create_llm_http_client(
            timeout_seconds=self.timeout_seconds
        )

    @property
    def endpoint(self) -> str:
        return chat_completions_url(self.base_url)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        prompt: str,
        system_prompt: str | None,
        *,
        stream: bool,
        temperature: float,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens,
            "stream": stream,
        }

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        payload = self._payload(
            prompt,
            system_prompt,
            stream=False,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        data = await self._request_json(payload)
        return self._extract_content(data)

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        payload = self._payload(
            prompt,
            system_prompt,
            stream=True,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        async for chunk in self._request_stream(payload):
            yield chunk

    async def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        attempts = max(1, self.max_retries)

        for attempt in range(attempts):
            try:
                response = await self._client.post(
                    self.endpoint,
                    headers=self._headers(),
                    json=payload,
                )
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(
                    "LLM provider timeout",
                    extra={"provider": self.name, "attempt": attempt + 1},
                )
                if attempt + 1 >= attempts:
                    raise LLMProviderError(
                        "LLM request timed out.",
                        details={"provider": self.name},
                    ) from exc
                await self._backoff(attempt)
                continue
            except httpx.RequestError as exc:
                last_error = exc
                logger.warning(
                    "LLM provider connection error",
                    extra={"provider": self.name, "attempt": attempt + 1},
                )
                if attempt + 1 >= attempts:
                    raise LLMProviderError(
                        "LLM provider connection failed.",
                        details={"provider": self.name},
                    ) from exc
                await self._backoff(attempt)
                continue

            if response.status_code in RETRYABLE_STATUS:
                logger.warning(
                    "LLM provider retryable status",
                    extra={
                        "provider": self.name,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    },
                )
                if attempt + 1 >= attempts:
                    raise LLMProviderError(
                        "LLM provider request failed.",
                        details={
                            "provider": self.name,
                            "status_code": response.status_code,
                        },
                    )
                await self._backoff(attempt)
                continue

            if response.status_code in NON_RETRYABLE_STATUS:
                raise LLMProviderError(
                    "LLM provider request was rejected.",
                    details={
                        "provider": self.name,
                        "status_code": response.status_code,
                    },
                )

            if response.status_code >= 400:
                raise LLMProviderError(
                    "LLM provider request failed.",
                    details={
                        "provider": self.name,
                        "status_code": response.status_code,
                    },
                )

            try:
                data = response.json()
            except json.JSONDecodeError as exc:
                raise LLMProviderError(
                    "LLM provider returned malformed JSON.",
                    details={"provider": self.name},
                ) from exc

            if not isinstance(data, dict):
                raise LLMProviderError(
                    "LLM provider returned an invalid response schema.",
                    details={"provider": self.name},
                )
            return data

        raise LLMProviderError(
            "LLM provider request failed.",
            details={"provider": self.name},
        ) from last_error

    async def _request_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        try:
            async with self._client.stream(
                "POST",
                self.endpoint,
                headers=self._headers(),
                json=payload,
            ) as response:
                if response.status_code in NON_RETRYABLE_STATUS:
                    raise LLMProviderError(
                        "LLM provider request was rejected.",
                        details={
                            "provider": self.name,
                            "status_code": response.status_code,
                        },
                    )
                if response.status_code >= 400:
                    raise LLMProviderError(
                        "LLM provider request failed.",
                        details={
                            "provider": self.name,
                            "status_code": response.status_code,
                        },
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                    else:
                        continue
                    if data_str == "[DONE]":
                        break
                    try:
                        payload_obj = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    content = self._extract_delta(payload_obj)
                    if content:
                        yield content
        except LLMProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                "LLM request timed out.",
                details={"provider": self.name},
            ) from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(
                "LLM provider connection failed.",
                details={"provider": self.name},
            ) from exc
        except asyncio.CancelledError:
            raise

    def _extract_content(self, data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(
                "LLM provider returned no assistant content.",
                details={"provider": self.name},
            )
        first = choices[0]
        if not isinstance(first, dict):
            raise LLMProviderError(
                "LLM provider returned an invalid response schema.",
                details={"provider": self.name},
            )
        message = first.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        text = first.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
        raise LLMProviderError(
            "LLM provider returned no assistant content.",
            details={"provider": self.name},
        )

    def _extract_delta(self, data: dict[str, Any]) -> str | None:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0]
        if not isinstance(first, dict):
            return None
        delta = first.get("delta")
        if isinstance(delta, dict):
            content = delta.get("content")
            if isinstance(content, str) and content:
                return content
        message = first.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content:
                return content
        return None

    async def _backoff(self, attempt: int) -> None:
        delay = min(8.0, 2**attempt)
        await asyncio.sleep(delay)
