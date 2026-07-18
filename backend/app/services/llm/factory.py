from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.llama import LlamaProvider
from app.services.llm.mistral import MistralProvider

SUPPORTED_PROVIDERS = {"gemini", "llama", "mistral"}


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """
    Resolve an LLM provider by name.

    Supported: gemini, llama, mistral.
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
    if name == "llama":
        return LlamaProvider()
    if name == "mistral":
        return MistralProvider()

    raise ValidationAppError(
        f"Provider '{name}' is not implemented yet.",
        details={"supported": sorted(SUPPORTED_PROVIDERS)},
    )
