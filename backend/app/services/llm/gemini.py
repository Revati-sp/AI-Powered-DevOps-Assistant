from __future__ import annotations

import asyncio
from typing import Any

import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self, api_key: str | None = None, model_name: str | None = None
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.timeout_seconds = settings.effective_llm_timeout

        if not self.api_key:
            raise LLMProviderError(
                "GEMINI_API_KEY is not configured.",
                details={"provider": self.name},
            )

        genai.configure(api_key=self.api_key)
        self._model_name = self.model_name

    def _build_model(self, system_prompt: str | None) -> Any:
        if system_prompt:
            try:
                return genai.GenerativeModel(
                    self._model_name,
                    system_instruction=system_prompt,
                )
            except TypeError:
                return genai.GenerativeModel(self._model_name)
        return genai.GenerativeModel(self._model_name)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        model = self._build_model(system_prompt)
        contents = prompt
        # Fallback for SDKs that ignore system_instruction.
        if system_prompt and "system_instruction" not in getattr(
            model, "_generation_methods", {}
        ):
            # Keep prompt self-contained when system instruction unsupported.
            contents = f"{system_prompt}\n\n{prompt}"

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    model.generate_content,
                    contents,
                    generation_config=generation_config,
                ),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            logger.exception("Gemini request timed out")
            raise LLMProviderError(
                "LLM request timed out.",
                details={"provider": self.name},
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gemini request failed")
            raise LLMProviderError(
                "LLM provider request failed.",
                details={"provider": self.name},
            ) from exc

        text = getattr(response, "text", None)
        if not text:
            raise LLMProviderError(
                "LLM provider returned an empty response.",
                details={"provider": self.name},
            )
        return text.strip()
