"""Tests for BlindSpotEngine execution."""

import pytest
from blindspot.core.engine import BlindSpotEngine, GuardrailViolationError
from blindspot.providers.base import BaseLLMProvider
from blindspot.providers.heuristic_mock import HeuristicMockProvider


class MockBadRecommendationProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock_violator"

    def generate(self, user_prompt, system_prompt, temperature=0.2, **kwargs) -> str:
        return """
        {
          "decision_summary": "You are deciding between options.",
          "core_tension": "Tension exists.",
          "assumptions": [
            {
              "classification": "OBSERVATION",
              "detected": "You should choose Option A because it is much better.",
              "why_it_matters": "Significant difference",
              "missing_evidence_or_assumption": "None",
              "investigative_question": "Why?"
            }
          ],
          "overlooked_factors": [],
          "contradictions": [],
          "evidence_gaps": [],
          "tradeoffs": [],
          "questions_to_explore": []
        }
        """


def test_engine_analyze_with_heuristic_provider():
    engine = BlindSpotEngine(default_provider=HeuristicMockProvider())
    result = engine.analyze(
        user_input="I want to quit my job to build an indie SaaS. My spouse wants security, but I feel I can definitely make $20k MRR in 3 months.",
        options=["Quit job now", "Stay at day job and build on weekends"],
        context="Priorities: Financial stability for family, personal creative autonomy"
    )

    assert result.decision_summary is not None
    assert result.core_tension is not None
    assert len(result.assumptions) >= 1
    assert len(result.questions_to_explore) >= 1
    assert result.metadata["guardrails_passed"] is True
    assert result.metadata["provider"] == "heuristic"


def test_engine_raises_on_guardrail_violation_in_strict_mode():
    violating_engine = BlindSpotEngine(
        default_provider=MockBadRecommendationProvider(),
        strict_guardrails=True,
        max_retries=0
    )

    with pytest.raises(GuardrailViolationError) as exc_info:
        violating_engine.analyze(user_input="Help me think through Option A vs Option B")

    assert "NO_RECOMMENDATION" in str(exc_info.value.report.violations[0].rule)


def test_engine_passes_with_warnings_in_non_strict_mode():
    violating_engine = BlindSpotEngine(
        default_provider=MockBadRecommendationProvider(),
        strict_guardrails=False,
        max_retries=0
    )

    result = violating_engine.analyze(user_input="Help me think through Option A vs Option B")
    assert result.metadata["guardrails_passed"] is False
    assert result.metadata["violations_count"] > 0


def test_provider_factory_caching():
    from blindspot.providers.factory import get_provider, clear_provider_cache
    clear_provider_cache()
    p1 = get_provider("heuristic")
    p2 = get_provider("heuristic")
    assert p1 is p2
    clear_provider_cache()
    p3 = get_provider("heuristic")
    assert p3 is not p1
