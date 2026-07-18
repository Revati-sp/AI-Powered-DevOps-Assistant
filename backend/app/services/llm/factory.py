from __future__ import annotations

import os

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.llama import LlamaProvider
from app.services.llm.mistral import MistralProvider

SUPPORTED_PROVIDERS = {"gemini", "llama", "mistral"}


def is_provider_env_configured(provider_name: str) -> bool:
    settings = get_settings()
    mapping = {
        "gemini": settings.gemini_api_key,
        "llama": settings.llama_api_key,
        "mistral": settings.mistral_api_key,
    }
    return bool(mapping.get(provider_name, "").strip())


def get_llm_provider(
    provider_name: str | None = None,
    *,
    require_enabled: bool = True,
) -> LLMProvider:
    """
    Resolve an LLM provider by name.

    Supported: gemini, llama, mistral.
    When require_enabled is True, providers without configured credentials are rejected.
    """
    settings = get_settings()
    name = (provider_name or settings.llm_provider).lower().strip()

    if name not in SUPPORTED_PROVIDERS:
        raise ValidationAppError(
            f"Unsupported LLM provider '{name}'.",
            details={"supported": sorted(SUPPORTED_PROVIDERS)},
        )

    if require_enabled and not is_provider_env_configured(name):
        raise ValidationAppError(
            f"Provider '{name}' is not configured.",
            details={"provider": name},
        )

    if name == "gemini":
        return GeminiProvider()
    if name == "llama":
        return LlamaProvider()
    if name == "mistral":
        return MistralProvider()

    raise ValidationAppError(
        f"Provider '{name}' is not implemented yet.",
        details={"supported": sorted(SUPPORTED_PROVIDERS)},
    )


def get_llm_provider_from_env_keys(
    provider_name: str,
    *,
    secret_env_key: str,
    base_url_env_key: str | None = None,
    model_env_key: str | None = None,
) -> LLMProvider:
    """Build a provider using env-var references instead of stored secrets."""
    name = provider_name.lower().strip()
    if name not in SUPPORTED_PROVIDERS:
        raise ValidationAppError(
            f"Unsupported LLM provider '{name}'.",
            details={"supported": sorted(SUPPORTED_PROVIDERS)},
        )
    if not os.environ.get(secret_env_key, "").strip():
        raise ValidationAppError(
            f"Provider '{name}' secret env var '{secret_env_key}' is not set.",
            details={"secret_env_key": secret_env_key},
        )
    return get_llm_provider(name, require_enabled=False)
