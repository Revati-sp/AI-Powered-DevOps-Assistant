from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


def chunk_text(text: str, *, max_chunk_chars: int = 48) -> list[str]:
    """Split text into bounded word-aware chunks for streaming fallback."""
    content = text.strip()
    if not content:
        return []

    chunks: list[str] = []
    current = ""
    for token in content.split(" "):
        piece = token if not current else f" {token}"
        if current and len(current) + len(piece) > max_chunk_chars:
            chunks.append(current)
            current = token
        else:
            current += piece
    if current:
        chunks.append(current)
    return chunks


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

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Stream a completion.

        Default fallback generates the full response and yields word-aware chunks.
        """
        text = await self.generate(
            prompt,
            system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        for chunk in chunk_text(text):
            yield chunk
