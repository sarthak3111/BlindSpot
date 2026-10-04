"""BlindSpot - AI Critical-Thinking & Decision Quality Analysis Engine."""

from blindspot.core.models import (
    ClassificationType,
    BlindSpotItem,
    AnalysisResult,
    AnalysisRequest,
)
from blindspot.core.engine import BlindSpotEngine, GuardrailViolationError
from blindspot.core.guardrails import GuardrailValidator, GuardrailReport
from blindspot.core.system_prompt import SYSTEM_ROLE_PROMPT

__version__ = "0.1.0"

__all__ = [
    "BlindSpotEngine",
    "AnalysisResult",
    "AnalysisRequest",
    "BlindSpotItem",
    "ClassificationType",
    "GuardrailValidator",
    "GuardrailReport",
    "GuardrailViolationError",
    "SYSTEM_ROLE_PROMPT",
]
