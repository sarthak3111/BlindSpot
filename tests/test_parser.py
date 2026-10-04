"""Tests for parser module."""

import pytest
from blindspot.core.parser import parse_analysis_response, extract_json_str, clean_json_text, ResponseParsingError
from blindspot.core.models import ClassificationType


def test_parse_clean_json():
    raw = """
    {
      "decision_summary": "Decision between A and B",
      "core_tension": "Cost vs Quality",
      "assumptions": [
        {
          "classification": "OBSERVATION",
          "detected": "Cost is fixed",
          "why_it_matters": "Affects budget",
          "missing_evidence_or_assumption": "Vendor contract not finalized",
          "investigative_question": "Is the quote guaranteed?"
        }
      ],
      "overlooked_factors": [],
      "contradictions": [],
      "evidence_gaps": [],
      "tradeoffs": [],
      "questions_to_explore": ["Can we negotiate terms?"]
    }
    """
    res = parse_analysis_response(raw)
    assert res.decision_summary == "Decision between A and B"
    assert res.core_tension == "Cost vs Quality"
    assert len(res.assumptions) == 1
    assert res.assumptions[0].classification == ClassificationType.OBSERVATION


def test_parse_markdown_fenced_json():
    raw = """
    Here is the analysis according to the BlindSpot framework:

    ```json
    {
      "decision_summary": "Choosing migration strategy",
      "core_tension": "Speed vs Architecture",
      "assumptions": [],
      "overlooked_factors": [],
      "contradictions": [],
      "evidence_gaps": [],
      "tradeoffs": [],
      "questions_to_explore": []
    }
    ```

    Hope this helps clarify your reasoning!
    """
    res = parse_analysis_response(raw)
    assert res.decision_summary == "Choosing migration strategy"
    assert res.core_tension == "Speed vs Architecture"


def test_parse_repair_trailing_commas():
    raw = """
    {
      "decision_summary": "Testing repairs",
      "core_tension": "Tension test",
      "assumptions": [],
      "overlooked_factors": [],
      "contradictions": [],
      "evidence_gaps": [],
      "tradeoffs": [],
      "questions_to_explore": [
        "Question 1",
      ],
    }
    """
    res = parse_analysis_response(raw)
    assert res.decision_summary == "Testing repairs"
    assert len(res.questions_to_explore) == 1


def test_parse_invalid_json_raises():
    raw = "Not json at all"
    with pytest.raises(ResponseParsingError):
        parse_analysis_response(raw)
