"""Tests for Flask REST API endpoints."""

import pytest
import json
from blindspot.api.app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "active_provider" in data


def test_schema_endpoint(client):
    resp = client.get("/api/schema")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "properties" in data
    assert "decision_summary" in data["properties"]
    assert "core_tension" in data["properties"]


def test_analyze_endpoint_missing_body(client):
    resp = client.post("/api/analyze", json={})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_analyze_endpoint_success(client):
    payload = {
        "user_input": "I am deciding whether to build our recommendation engine in-house or buy a SaaS solution. I think building it will take 2 weeks and save money.",
        "options": ["Build in-house", "Buy SaaS"],
        "context": "Timeline constraint: 2 months to release"
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "decision_summary" in data
    assert "core_tension" in data
    assert "assumptions" in data
    assert "overlooked_factors" in data
    assert "contradictions" in data
    assert "evidence_gaps" in data
    assert "tradeoffs" in data
    assert "questions_to_explore" in data
    assert "metadata" in data


def test_web_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BlindSpot" in resp.data
