"""Tests for the FastAPI wrapper.

These do NOT call the real LLM — the /triage handler's ``triage`` function is
monkey-patched to a fixed-state stub.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from claims_triage.state import (
    AgentTrace,
    ClaimIntake,
    CoverageDecision,
    SeverityAssessment,
    TriageRecommendation,
    TriageState,
)

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_triage_endpoint_returns_recommendation(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_state = TriageState(
        raw_fnol="Mock FNOL text",
        intake=ClaimIntake(
            policy_number="MM-PL-44721",
            claimant="Acme Logistics Inc.",
            loss_date="2026-03-14",
            loss_type="tractor-trailer rollover",
            description="Mock description for test.",
            severity_indicators=["hospitalisation", "third-party involvement"],
            needs_clarification=False,
        ),
        coverage=CoverageDecision(
            covered=True,
            policy_in_force=True,
            exclusions_triggered=[],
            reasoning="Mock coverage decision.",
            confidence=0.95,
        ),
        severity=SeverityAssessment(
            severity="high",
            rationale="Mock severity rationale.",
            indicators=["bodily injury with hospitalisation"],
            confidence=0.92,
        ),
        recommendation=TriageRecommendation(
            recommended_action="route_to_specialist",
            specialist_team="Casualty - North American Trucking",
            reasoning="Mock routing reasoning.",
            confidence=0.94,
        ),
        trace=[
            AgentTrace(
                agent_name="intake",
                started_at_iso="2026-05-12T10:00:00+00:00",
                finished_at_iso="2026-05-12T10:00:01+00:00",
                input_summary="mock input",
                output_summary="mock output",
                tokens_in=100,
                tokens_out=50,
            ),
        ],
    )

    def _fake_triage(raw_fnol: str) -> TriageState:
        assert raw_fnol == "Mock FNOL text"
        return fixed_state

    monkeypatch.setattr("api.main.triage", _fake_triage)

    response = client.post("/triage", json={"raw_fnol": "Mock FNOL text"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation"]["recommended_action"] == "route_to_specialist"
    assert payload["recommendation"]["specialist_team"] == "Casualty - North American Trucking"
    assert payload["severity"]["severity"] == "high"
    assert payload["coverage"]["covered"] is True
    assert payload["intake"]["policy_number"] == "MM-PL-44721"
