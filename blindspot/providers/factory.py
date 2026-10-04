"""Provider factory for instantiating LLM backends."""

from __future__ import annotations
import os
from typing import Optional, Dict, Tuple, Any
from blindspot.providers.base import BaseLLMProvider
from blindspot.providers.heuristic_mock import HeuristicMockProvider
from blindspot.providers.gemini import GeminiProvider
from blindspot.providers.openai_compatible import OpenAICompatibleProvider
from blindspot.providers.anthropic import AnthropicProvider

_PROVIDER_CACHE: Dict[Tuple, BaseLLMProvider] = {}


def clear_provider_cache() -> None:
    """Clear cached provider instances (useful for testing or reconfiguration)."""
    _PROVIDER_CACHE.clear()


def get_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """Factory function to resolve and instantiate the requested or best-fit provider."""
    raw_name = (provider_name or os.getenv("BLINDSPOT_PROVIDER") or "").lower().strip()
    cache_key = (
        raw_name,
        model or "",
        api_key or "",
        bool(os.getenv("GEMINI_API_KEY")),
        bool(os.getenv("OPENAI_API_KEY")),
        bool(os.getenv("ANTHROPIC_API_KEY")),
        tuple(sorted((k, str(v)) for k, v in kwargs.items()))
    )

    if cache_key in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[cache_key]

    if raw_name == "gemini":
        instance = GeminiProvider(api_key=api_key, model=model, **kwargs)
    elif raw_name in ("openai", "groq", "ollama", "openrouter"):
        instance = OpenAICompatibleProvider(api_key=api_key, model=model, **kwargs)
    elif raw_name in ("anthropic", "claude"):
        instance = AnthropicProvider(api_key=api_key, model=model, **kwargs)
    elif raw_name in ("heuristic", "mock", "test"):
        instance = HeuristicMockProvider(model=model, **kwargs)
    elif os.getenv("GEMINI_API_KEY"):
        instance = GeminiProvider(api_key=api_key, model=model, **kwargs)
    elif os.getenv("OPENAI_API_KEY"):
        instance = OpenAICompatibleProvider(api_key=api_key, model=model, **kwargs)
    elif os.getenv("ANTHROPIC_API_KEY"):
        instance = AnthropicProvider(api_key=api_key, model=model, **kwargs)
    else:
        instance = HeuristicMockProvider(model=model, **kwargs)

    _PROVIDER_CACHE[cache_key] = instance
    return instance
