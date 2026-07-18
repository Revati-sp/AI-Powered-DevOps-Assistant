from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.llm.openai_compatible import OpenAICompatibleProvider


class MistralProvider(OpenAICompatibleProvider):
    name = "mistral"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            api_key=api_key if api_key is not None else settings.mistral_api_key,
            base_url=base_url or settings.mistral_base_url,
            model=model or settings.mistral_model,
            provider_name="mistral",
            api_key_env="MISTRAL_API_KEY",
            client=client,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
