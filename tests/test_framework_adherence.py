"""Tests verifying adherence to the BlindSpot reasoning framework requirements."""

import pytest
import re
from blindspot.core.engine import BlindSpotEngine
from blindspot.core.models import ClassificationType, BlindSpotItem
from blindspot.core.guardrails import GuardrailValidator


def test_framework_structured_json_keys():
    """Verify that output contains exact required top-level keys."""
    engine = BlindSpotEngine()
    result = engine.analyze(
        user_input="Should I move from New York to Austin? In Austin no state tax and rent is lower. But in NY my professional network is huge."
    )
    result_dict = result.to_dict()

    expected_keys = [
        "decision_summary",
        "core_tension",
        "assumptions",
        "overlooked_factors",
        "contradictions",
        "evidence_gaps",
        "tradeoffs",
        "questions_to_explore"
    ]

    for key in expected_keys:
        assert key in result_dict, f"Missing key in JSON response: {key}"


def test_framework_no_recommendation_and_no_ranking():
    """Verify that analysis never tells the user what to choose or ranks options."""
    engine = BlindSpotEngine()
    result = engine.analyze(
        user_input="I have an offer from Google for $300k and an offer from a Series A for $160k + 1%. Which should I choose? Tell me what to do.",
        options=["Google ($300k)", "Series A ($160k + 1%)"]
    )

    validator = GuardrailValidator()
    report = validator.validate(result)

    assert report.passed is True
    assert not report.has_critical

    # Convert all text to lower
    all_text = " ".join([
        result.decision_summary,
        result.core_tension,
        " ".join(result.questions_to_explore),
        " ".join(item.detected for item in result.assumptions),
        " ".join(item.why_it_matters for item in result.assumptions),
        " ".join(item.detected for item in result.tradeoffs)
    ]).lower()

    # Verify no choice command or recommendation
    assert "i recommend" not in all_text
    assert "you should choose" not in all_text
    assert "you should pick" not in all_text
    assert "the best option is" not in all_text
    assert "ranked #1" not in all_text
    assert "first choice is" not in all_text


def test_framework_blind_spot_item_four_facets_and_classification():
    """Verify that every blind spot item explains:
    - what was detected
    - why it matters
    - what evidence is missing or what assumption is involved
    - one question the user should investigate
    And has classification OBSERVATION or HYPOTHESIS.
    """
    engine = BlindSpotEngine()
    result = engine.analyze(
        user_input="We are considering switching our primary database from Postgres to MongoDB because a blog post said Mongo scales better for JSON documents.",
        options=["Keep Postgres", "Migrate to MongoDB"]
    )

    categories = [
        result.assumptions,
        result.overlooked_factors,
        result.contradictions,
        result.evidence_gaps,
        result.tradeoffs
    ]

    total_items = 0
    for category in categories:
        for item in category:
            total_items += 1
            # 1. Classification check
            assert item.classification in (ClassificationType.OBSERVATION, ClassificationType.HYPOTHESIS)
            
            # 2. What was detected
            assert item.detected and len(item.detected.strip()) > 5
            
            # 3. Why it matters
            assert item.why_it_matters and len(item.why_it_matters.strip()) > 5
            
            # 4. Evidence missing or assumption involved
            assert item.missing_evidence_or_assumption and len(item.missing_evidence_or_assumption.strip()) > 5
            
            # 5. One question to investigate
            assert item.investigative_question and len(item.investigative_question.strip()) > 5

    assert total_items > 0, "Engine must produce at least one grounded blind spot."


def test_framework_questions_to_explore_are_inquiries_not_directives():
    """Verify that questions to explore are inquiry-based (e.g. contain question marks or inquiry phrasing)."""
    engine = BlindSpotEngine()
    result = engine.analyze(
        user_input="I want to buy a house now because interest rates might go higher later, even though housing prices seem inflated in my city."
    )

    assert len(result.questions_to_explore) >= 2
    for q in result.questions_to_explore:
        assert "?" in q or any(q.lower().startswith(w) for w in ["what", "how", "which", "are", "under what", "have you", "is"])
        # Ensure questions don't say "You should"
        assert not re.search(r"\byou\s+should\s+(choose|buy|pick)\b", q.lower())
