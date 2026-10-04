"""Google Gemini provider implementation using REST API."""

from __future__ import annotations
import os
import requests
from typing import Optional, Dict, Any
from blindspot.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider supporting models such as gemini-2.5-flash, gemini-1.5-pro, etc."""

    DEFAULT_MODEL = "gemini-2.5-flash"
    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 45,
        **kwargs
    ):
        model_name = model or os.getenv("GEMINI_MODEL") or self.DEFAULT_MODEL
        super().__init__(model=model_name, **kwargs)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "gemini"

    def generate(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        **kwargs
    ) -> str:
        if not self.api_key:
            raise ValueError(
                "Gemini API key is missing. Set the 'GEMINI_API_KEY' environment variable or pass api_key to the provider."
            )

        url = self.API_URL_TEMPLATE.format(model=self.model, api_key=self.api_key)

        payload = {
            "system_instruction": {
                "parts": [
                    {"text": system_prompt}
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": user_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            # Extract generated content
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"No response candidates returned by Gemini: {data}")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise RuntimeError("Candidate content has no parts.")

            return parts[0].get("text", "")

        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                raise RuntimeError(
                    f"Gemini API error ({e.response.status_code}): {e.response.text}"
                ) from e
            raise RuntimeError(f"Network error communicating with Gemini API: {e}") from e
