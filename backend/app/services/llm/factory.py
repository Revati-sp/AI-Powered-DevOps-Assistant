from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider

SUPPORTED_PROVIDERS = {"gemini"}


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """
    Resolve an LLM provider by name.

    Additional providers (e.g. llama, mistral) can be registered here later
    without changing API routes.
    """
    settings = get_settings()
    name = (provider_name or settings.llm_provider).lower().strip()

    if name not in SUPPORTED_PROVIDERS:
        raise ValidationAppError(
            f"Unsupported LLM provider '{name}'.",
            details={"supported": sorted(SUPPORTED_PROVIDERS)},
        )

    if name == "gemini":
        return GeminiProvider()

    raise ValidationAppError(
        f"Provider '{name}' is not implemented yet.",
        details={"supported": sorted(SUPPORTED_PROVIDERS)},
    )
