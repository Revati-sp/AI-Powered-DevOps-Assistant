from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM provider interface for multi-provider support."""

    name: str

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        """Generate a text completion from the provider."""
