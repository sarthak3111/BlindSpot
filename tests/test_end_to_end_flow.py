"""Comprehensive End-to-End flow verification test."""

import pytest
import json
from pathlib import Path
from blindspot.api.app import create_app
from blindspot.core.parser import parse_analysis_response, clean_json_text
from blindspot.core.models import ClassificationType
from blindspot.cli.main import format_cli_output


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_e2e_all_example_scenarios(client):
    """Test the complete API flow on all example files, verifying every section."""
    example_files = list(Path("examples").glob("*.json"))
    assert len(example_files) >= 3, "Expected at least 3 example scenarios"

    for file_path in example_files:
        payload = json.loads(file_path.read_text(encoding="utf-8"))

        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200, f"Failed for {file_path.name}: {response.get_json()}"

        data = response.get_json()

        # 1. Decision summary section
        assert "decision_summary" in data
        assert isinstance(data["decision_summary"], str)
        assert len(data["decision_summary"].strip()) > 10

        # 2. Core tension section
        assert "core_tension" in data
        assert isinstance(data["core_tension"], str)
        assert len(data["core_tension"].strip()) > 10

        # 3. Blind spot categories
        categories = ["assumptions", "overlooked_factors", "contradictions", "evidence_gaps", "tradeoffs"]
        total_items = 0

        for cat in categories:
            assert cat in data, f"Missing category {cat}"
            assert isinstance(data[cat], list)
            for item in data[cat]:
                total_items += 1
                assert item["classification"] in ("OBSERVATION", "HYPOTHESIS")
                assert "detected" in item and len(item["detected"].strip()) > 0
                assert "why_it_matters" in item and len(item["why_it_matters"].strip()) > 0
                assert "missing_evidence_or_assumption" in item and len(item["missing_evidence_or_assumption"].strip()) > 0
                assert "investigative_question" in item and len(item["investigative_question"].strip()) > 0

        assert total_items > 0, f"Expected detected blind spots for {file_path.name}"

        # 4. Questions to explore
        assert "questions_to_explore" in data
        assert isinstance(data["questions_to_explore"], list)
        assert len(data["questions_to_explore"]) >= 1
        for q in data["questions_to_explore"]:
            assert isinstance(q, str)
            assert len(q.strip()) > 5

        # 5. Metadata
        assert "metadata" in data
        assert data["metadata"]["guardrails_passed"] is True


def test_e2e_json_cleaning_and_quirk_repair():
    """Verify parser repairs comments, smart quotes, trailing commas, and fences."""
    quirky_raw = """
    Here is the completed analysis:
    ```json
    {
      // Stated summary
      “decision_summary”: “Evaluating transition from monolithic server to microservices.”,
      /* Core tension block */
      “core_tension”: “Execution velocity versus architectural complexity.”,
      “assumptions”: [
        {
          “classification”: “OBSERVATION” or “HYPOTHESIS”,
          “detected”: “Claim that modern tech stack will guarantee hiring success.”,
          “why_it_matters”: “May introduce unneeded operational overhead.”,
          “missing_evidence_or_assumption”: “Empirical evidence on hiring pipelines is missing.”,
          “investigative_question”: “What candidates have refused offers based on the stack?”,
        },
      ],
      “overlooked_factors”: [],
      “contradictions”: [],
      “evidence_gaps”: [],
      “tradeoffs”: [],
      “questions_to_explore”: [
        “Can the team deliver the milestone while refactoring?”,
      ],
    }
    ```
    Best of luck with your decision.
    """
    result = parse_analysis_response(quirky_raw)
    assert result.decision_summary == "Evaluating transition from monolithic server to microservices."
    assert result.core_tension == "Execution velocity versus architectural complexity."
    assert len(result.assumptions) == 1
    assert result.assumptions[0].classification == ClassificationType.OBSERVATION
    assert len(result.questions_to_explore) == 1


def test_e2e_web_dom_elements_exist(client):
    """Verify that every DOM element used by JavaScript exists in index.html."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    expected_ids = [
        "userInput",
        "optionsInput",
        "contextInput",
        "providerSelect",
        "temperatureInput",
        "analyzeBtn",
        "btnText",
        "btnSpinner",
        "emptyState",
        "resultsContainer",
        "resSummary",
        "resTension",
        "resMetadata",
        "categoryCards",
        "resQuestions",
        "rawJsonSection",
        "rawJsonContent",
        "errorAlert",
        "errorMessage",
        "errorTitle",
        "copyBtn"
    ]

    for elem_id in expected_ids:
        assert f'id="{elem_id}"' in html, f"Missing expected DOM id '{elem_id}' in index.html"


def test_api_security_input_validation(client):
    """Verify server-side security checks: input type, length limits, and temperature handling."""
    # 1. Non-string user_input rejected
    r1 = client.post("/api/analyze", json={"user_input": 12345})
    assert r1.status_code == 400
    assert "must be a string" in r1.get_json()["error"]

    # 2. Oversized user_input rejected
    r2 = client.post("/api/analyze", json={"user_input": "x" * 50001})
    assert r2.status_code == 400
    assert "exceeds maximum allowed size" in r2.get_json()["error"]

    # 3. Non-numeric temperature safely coerced without crashing
    r3 = client.post("/api/analyze", json={
        "user_input": "Test reasoning with invalid temperature",
        "temperature": "invalid_temp_string"
    })
    assert r3.status_code == 200

    # 4. Oversized options list rejected
    r4 = client.post("/api/analyze", json={
        "user_input": "Test reasoning with too many options",
        "options": [f"Option {i}" for i in range(25)]
    })
    assert r4.status_code == 400
    assert "maximum of 20 options" in r4.get_json()["error"]


def test_e2e_cli_formatting_renders_all_sections():
    """Verify that CLI output renderer formats all sections clearly."""
    example_path = Path("examples/career_crossroads.json")
    payload = json.loads(example_path.read_text(encoding="utf-8"))

    from blindspot.core.engine import BlindSpotEngine
    engine = BlindSpotEngine()
    result = engine.analyze(
        user_input=payload["user_input"],
        options=payload.get("options"),
        context=payload.get("context")
    )

    formatted = format_cli_output(result)
    assert "DECISION SUMMARY:" in formatted
    assert "CORE TENSION:" in formatted
    assert "ASSUMPTIONS" in formatted
    assert "OVERLOOKED FACTORS" in formatted
    assert "CONTRADICTIONS & TENSIONS" in formatted
    assert "EVIDENCE GAPS" in formatted
    assert "TRADE-OFFS" in formatted
    assert "KEY QUESTIONS TO EXPLORE:" in formatted
    assert "Why It Matters:" in formatted
    assert "Evidence/Assumption:" in formatted
    assert "Investigative Question:" in formatted
