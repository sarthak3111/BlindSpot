"""Provider factory for instantiating LLM backends."""

from __future__ import annotations
import os
from typing import Optional
from blindspot.providers.base import BaseLLMProvider
from blindspot.providers.heuristic_mock import HeuristicMockProvider
from blindspot.providers.gemini import GeminiProvider
from blindspot.providers.openai_compatible import OpenAICompatibleProvider
from blindspot.providers.anthropic import AnthropicProvider


def get_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """Factory function to resolve and instantiate the requested or best-fit provider."""
    name = (provider_name or os.getenv("BLINDSPOT_PROVIDER") or "").lower().strip()

    if name == "gemini":
        return GeminiProvider(api_key=api_key, model=model, **kwargs)
    elif name in ("openai", "groq", "ollama", "openrouter"):
        return OpenAICompatibleProvider(api_key=api_key, model=model, **kwargs)
    elif name in ("anthropic", "claude"):
        return AnthropicProvider(api_key=api_key, model=model, **kwargs)
    elif name in ("heuristic", "mock", "test"):
        return HeuristicMockProvider(model=model, **kwargs)

    # Automatic detection based on available environment variables
    if os.getenv("GEMINI_API_KEY"):
        return GeminiProvider(api_key=api_key, model=model, **kwargs)
    elif os.getenv("OPENAI_API_KEY"):
        return OpenAICompatibleProvider(api_key=api_key, model=model, **kwargs)
    elif os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicProvider(api_key=api_key, model=model, **kwargs)

    # Default fallback to heuristic mock provider
    return HeuristicMockProvider(model=model, **kwargs)
