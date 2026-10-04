"""Anthropic Claude LLM provider implementation."""

from __future__ import annotations
import os
import requests
from typing import Optional, Dict, Any
from blindspot.providers.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Provider for Anthropic Claude models (e.g. claude-3-7-sonnet-20250219, claude-3-5-haiku-20241022)."""

    DEFAULT_MODEL = "claude-3-5-haiku-20241022"
    API_URL = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 45,
        **kwargs
    ):
        model_name = model or os.getenv("ANTHROPIC_MODEL") or self.DEFAULT_MODEL
        super().__init__(model=model_name, **kwargs)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def generate(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        **kwargs
    ) -> str:
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is missing. Set the 'ANTHROPIC_API_KEY' environment variable or provide api_key."
            )

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION
        }

        # Prompt Anthropic to return pure JSON
        full_system_prompt = system_prompt + "\nYou MUST reply with raw JSON only. No markdown formatting, no preamble."

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": full_system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            resp = self.session.post(self.API_URL, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            content_blocks = data.get("content", [])
            text_blocks = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            return "\n".join(text_blocks)

        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                raise RuntimeError(
                    f"Anthropic API error ({e.response.status_code}): {e.response.text}"
                ) from e
            raise RuntimeError(f"Network error communicating with Anthropic API: {e}") from e
