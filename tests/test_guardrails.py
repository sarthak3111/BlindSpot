"""Tests for GuardrailValidator compliance enforcement."""

import pytest
from blindspot.core.guardrails import GuardrailValidator, ViolationSeverity
from blindspot.core.models import AnalysisResult, BlindSpotItem, ClassificationType


@pytest.fixture
def compliant_result():
    return AnalysisResult(
        decision_summary="User is deliberating between Offer A and Offer B.",
        core_tension="Short-term cash compensation versus long-term upside potential.",
        assumptions=[
            BlindSpotItem(
                classification=ClassificationType.OBSERVATION,
                detected="User stated equity will 10x in 2 years",
                why_it_matters="Overconfidence in speculative valuation leads to underhedged risk",
                missing_evidence_or_assumption="Assumes startup market cap trajectories are linear",
                investigative_question="What comparable exits exist in this sector over the past 3 years?"
            )
        ],
        overlooked_factors=[],
        contradictions=[],
        evidence_gaps=[],
        tradeoffs=[
            BlindSpotItem(
                classification=ClassificationType.HYPOTHESIS,
                detected="Sacrificing personal leisure time for professional advancement",
                why_it_matters="May compound relationship friction",
                missing_evidence_or_assumption="Assumes partner will absorb household management burden indefinitely",
                investigative_question="Have explicit weekly expectations been agreed upon?"
            )
        ],
        questions_to_explore=[
            "What would cause you to re-evaluate this choice after 12 months?"
        ]
    )


def test_guardrails_pass_on_compliant_result(compliant_result):
    validator = GuardrailValidator()
    report = validator.validate(compliant_result)
    assert report.passed is True
    assert len(report.violations) == 0


def test_guardrail_catches_explicit_recommendation(compliant_result):
    compliant_result.decision_summary = "User is choosing. I recommend picking Option A because it has higher upside."
    validator = GuardrailValidator()
    report = validator.validate(compliant_result)

    assert report.passed is False
    assert report.has_critical is True
    assert any(v.rule == "NO_RECOMMENDATION" for v in report.violations)


def test_guardrail_catches_you_should_choose(compliant_result):
    compliant_result.core_tension = "You should choose the startup option to maximize your potential."
    validator = GuardrailValidator()
    report = validator.validate(compliant_result)

    assert report.passed is False
    assert any(v.rule == "NO_RECOMMENDATION" for v in report.violations)


def test_guardrail_catches_ranking(compliant_result):
    compliant_result.questions_to_explore.append("Option A is ranked #1 because of the upside.")
    validator = GuardrailValidator()
    report = validator.validate(compliant_result)

    assert report.passed is False
    assert any(v.rule == "NO_RANKING" for v in report.violations)


def test_guardrail_catches_empty_detected_field(compliant_result):
    compliant_result.assumptions.append(
        BlindSpotItem(
            classification=ClassificationType.HYPOTHESIS,
            detected="   ",  # Invalid empty
            why_it_matters="Matters a lot",
            missing_evidence_or_assumption="None",
            investigative_question="What?"
        )
    )
    validator = GuardrailValidator()
    report = validator.validate(compliant_result)

    assert report.passed is False
    assert any(v.rule == "INSUFFICIENT_DETECTION" for v in report.violations)
