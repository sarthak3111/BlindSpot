"""OpenAI-compatible LLM provider implementation."""

from __future__ import annotations
import os
import requests
from typing import Optional, Dict, Any
from blindspot.providers.base import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for OpenAI and OpenAI-compatible endpoints (Groq, Ollama, OpenRouter, vLLM)."""

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 45,
        **kwargs
    ):
        model_name = model or os.getenv("OPENAI_MODEL") or self.DEFAULT_MODEL
        super().__init__(model=model_name, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "openai"

    def generate(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        **kwargs
    ) -> str:
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            raise ValueError(
                "OpenAI API key is missing. Set the 'OPENAI_API_KEY' environment variable or provide api_key."
            )

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'no-key-required'}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"No choices returned by endpoint: {data}")

            message = choices[0].get("message", {})
            return message.get("content", "")

        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                raise RuntimeError(
                    f"OpenAI-compatible API error ({e.response.status_code}): {e.response.text}"
                ) from e
            raise RuntimeError(f"Network error communicating with endpoint: {e}") from e
