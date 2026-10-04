"""Core BlindSpot AI Analysis Engine orchestrator."""

from __future__ import annotations
import time
import logging
from typing import Optional, List, Dict, Any, Union

from blindspot.core.models import AnalysisRequest, AnalysisResult
from blindspot.core.system_prompt import SYSTEM_ROLE_PROMPT, format_user_prompt
from blindspot.core.parser import parse_analysis_response, ResponseParsingError
from blindspot.core.guardrails import GuardrailValidator, GuardrailReport
from blindspot.providers.base import BaseLLMProvider
from blindspot.providers.factory import get_provider

logger = logging.getLogger("blindspot.engine")


class GuardrailViolationError(ValueError):
    """Raised when an analysis output violates critical BlindSpot guardrails in strict mode."""
    def __init__(self, message: str, report: GuardrailReport):
        super().__init__(message)
        self.report = report


class BlindSpotEngine:
    """The central AI analysis engine implementing the BlindSpot critical-thinking framework."""

    def __init__(
        self,
        default_provider: Optional[BaseLLMProvider] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        strict_guardrails: bool = True,
        max_retries: int = 1,
        **provider_kwargs
    ):
        if default_provider:
            self.provider = default_provider
        else:
            self.provider = get_provider(
                provider_name=provider_name,
                model=model,
                api_key=api_key,
                **provider_kwargs
            )
        self.strict_guardrails = strict_guardrails
        self.max_retries = max_retries
        self.validator = GuardrailValidator()

    def analyze(
        self,
        user_input: Union[str, AnalysisRequest],
        options: Optional[List[str]] = None,
        context: Optional[str] = None,
        provider: Optional[BaseLLMProvider] = None,
        temperature: float = 0.2,
        strict: Optional[bool] = None
    ) -> AnalysisResult:
        """Execute a complete BlindSpot analysis on the user's reasoning.
        
        Args:
            user_input: Raw reasoning text or an AnalysisRequest instance.
            options: Optional list of explicit choices considered.
            context: Additional background or stated priorities.
            provider: Override the default provider for this analysis call.
            temperature: Sampling temperature (default: 0.2).
            strict: Override strict guardrail enforcement.
            
        Returns:
            Structured AnalysisResult conforming strictly to the BlindSpot framework.
        """
        start_time = time.perf_counter()

        # Coerce request
        if isinstance(user_input, AnalysisRequest):
            req = user_input
        else:
            req = AnalysisRequest(
                user_input=user_input,
                options=options,
                context=context,
                temperature=temperature,
                strict_guardrails=strict if strict is not None else self.strict_guardrails
            )

        active_provider = provider or self.provider
        prompt = format_user_prompt(
            user_input=req.user_input,
            context=req.context,
            options=req.options
        )

        attempts = 0
        last_error = None
        current_prompt = prompt

        while attempts <= self.max_retries:
            attempts += 1
            try:
                raw_response = active_provider.generate(
                    user_prompt=current_prompt,
                    system_prompt=SYSTEM_ROLE_PROMPT,
                    temperature=req.temperature
                )

                # Parse JSON into structured schema
                result = parse_analysis_response(raw_response)

                # Validate guardrails
                guardrail_report = self.validator.validate(result, user_input=req.user_input)

                # Check for critical violations
                if guardrail_report.has_critical:
                    err_msg = "; ".join(v.message for v in guardrail_report.violations if v.severity == "CRITICAL")
                    if attempts <= self.max_retries and active_provider.provider_name != "heuristic":
                        # Attempt self-correction retry
                        logger.warning("Guardrail violation detected: %s. Retrying with feedback...", err_msg)
                        current_prompt = (
                            f"{prompt}\n\n"
                            f"CRITICAL COMPLIANCE ERROR IN PREVIOUS ATTEMPT:\n"
                            f"{err_msg}\n"
                            f"REMINDER: You MUST NOT recommend, rank, or tell the user which decision to make. "
                            f"Ensure every blind spot has classification 'OBSERVATION' or 'HYPOTHESIS' and all 4 required fields. "
                            f"Generate compliant JSON only."
                        )
                        continue

                    if req.strict_guardrails:
                        raise GuardrailViolationError(
                            f"Analysis output violated BlindSpot negative constraints: {err_msg}",
                            guardrail_report
                        )

                # Attach metadata
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                result.metadata = {
                    "provider": active_provider.provider_name,
                    "model": getattr(active_provider, "model", "unknown"),
                    "latency_ms": elapsed_ms,
                    "guardrails_passed": guardrail_report.passed,
                    "violations_count": len(guardrail_report.violations),
                    "warnings_count": len(guardrail_report.warnings),
                    "warnings": [w.message for w in guardrail_report.warnings]
                }

                return result

            except ResponseParsingError as rpe:
                last_error = rpe
                if attempts <= self.max_retries and active_provider.provider_name != "heuristic":
                    logger.warning("Parsing failed: %s. Retrying...", rpe)
                    current_prompt = f"{prompt}\n\nPREVIOUS RESPONSE WAS NOT VALID JSON. Output valid JSON matching the exact schema."
                    continue
                raise

        raise RuntimeError(f"BlindSpot analysis failed after {attempts} attempts. Last error: {last_error}")
