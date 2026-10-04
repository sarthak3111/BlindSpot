"""Base provider interface for LLM backends."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for all BlindSpot LLM execution providers."""

    def __init__(self, model: Optional[str] = None, **kwargs):
        self.model = model
        self.config = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider backend."""
        pass

    @abstractmethod
    def generate(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        **kwargs
    ) -> str:
        """Execute text completion and return raw output string.
        
        Args:
            user_prompt: Formatted user reasoning text.
            system_prompt: The BlindSpot system instruction prompt.
            temperature: Sampling temperature.
            
        Returns:
            Raw response text (expected to be JSON).
        """
        pass
