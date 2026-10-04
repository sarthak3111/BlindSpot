"""Tests for BlindSpot Pydantic models and schemas."""

import pytest
from blindspot.core.models import (
    ClassificationType,
    BlindSpotItem,
    AnalysisResult,
    AnalysisRequest,
)


def test_classification_type_normalization():
    item1 = BlindSpotItem(
        classification="OBSERVATION",
        detected="User stated they have a mortgage",
        why_it_matters="Financial obligation affects downside tolerance",
        missing_evidence_or_assumption="None; explicitly stated",
        investigative_question="How many months of liquid reserves are available?"
    )
    assert item1.classification == ClassificationType.OBSERVATION

    item2 = BlindSpotItem(
        classification="hypothesis",
        detected="Burnout risk may increase",
        why_it_matters="High attrition risk",
        missing_evidence_or_assumption="Assumes workload is unsustainable",
        investigative_question="What are historical overtime hours for this role?"
    )
    assert item2.classification == ClassificationType.HYPOTHESIS


def test_blindspot_item_alias_mapping():
    raw_data = {
        "type": "OBSERVATION",
        "what_detected": "Explicit claim regarding market growth",
        "impact": "Biases risk assessment",
        "evidence_missing": "Third party market validation",
        "question": "What is the TAM based on audited reports?"
    }
    item = BlindSpotItem(**raw_data)
    assert item.classification == ClassificationType.OBSERVATION
    assert item.detected == "Explicit claim regarding market growth"
    assert item.why_it_matters == "Biases risk assessment"
    assert item.missing_evidence_or_assumption == "Third party market validation"
    assert item.investigative_question == "What is the TAM based on audited reports?"


def test_analysis_result_schema_and_serialization():
    result = AnalysisResult(
        decision_summary="Evaluating whether to leave corporate role for startup.",
        core_tension="Known stability vs uncertain high-upside equity.",
        assumptions=[
            BlindSpotItem(
                classification=ClassificationType.OBSERVATION,
                detected="User claims startup will definitely succeed",
                why_it_matters="Treats high-variance gamble as guaranteed wealth",
                missing_evidence_or_assumption="Assumes macroeconomic tailwinds guarantee company survival",
                investigative_question="What failure rates exist for Series A startups in this vertical?"
            )
        ],
        overlooked_factors=[
            BlindSpotItem(
                classification=ClassificationType.HYPOTHESIS,
                detected="Loss of 401k employer match and healthcare subsidy",
                why_it_matters="Increases true compensation delta",
                missing_evidence_or_assumption="Total rewards comparison omitted",
                investigative_question="What is the net dollar difference including all benefits?"
            )
        ],
        contradictions=[],
        evidence_gaps=[],
        tradeoffs=[],
        questions_to_explore=[
            "What happens if the startup takes 7 years to exit?"
        ]
    )

    data = result.to_dict()
    # Verify exact keys requested by framework
    expected_keys = {
        "decision_summary",
        "core_tension",
        "assumptions",
        "overlooked_factors",
        "contradictions",
        "evidence_gaps",
        "tradeoffs",
        "questions_to_explore"
    }
    assert set(data.keys()) == expected_keys
    assert len(data["assumptions"]) == 1
    assert data["assumptions"][0]["classification"] == "OBSERVATION"
    assert "investigative_question" in data["assumptions"][0]

    # Test markdown export
    md = result.to_markdown()
    assert "# BlindSpot Analysis Report" in md
    assert "[OBSERVATION]" in md
