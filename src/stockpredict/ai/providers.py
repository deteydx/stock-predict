"""LLM provider abstraction: OpenAI and Claude."""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM completion providers."""

    async def complete(self, system: str, user: str) -> str:
        """Send a system + user message and return the assistant's response text."""
        ...


class OpenAIProvider:
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_completion_tokens=4096,
        )
        content = response.choices[0].message.content or ""
        logger.info("OpenAI response: %d chars (model=%s)", len(content), self._model)
        return content


class ClaudeProvider:
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0.3,
        )
        content = response.content[0].text if response.content else ""
        logger.info("Claude response: %d chars (model=%s)", len(content), self._model)
        return content


def create_provider(provider: str, settings) -> LLMProvider:
    """Factory to create the configured LLM provider."""
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    elif provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when AI_PROVIDER=claude")
        return ClaudeProvider(settings.anthropic_api_key, settings.claude_model)
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
