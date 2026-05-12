"""Tests for the TriageState pydantic models."""

import pytest
from pydantic import ValidationError

from claims_triage.state import (
    AgentTrace,
    ClaimIntake,
    CoverageDecision,
    SeverityAssessment,
    TriageRecommendation,
    TriageState,
)


def _fully_populated_state() -> TriageState:
    intake = ClaimIntake(
        policy_number="MM-PL-44721",
        claimant="Acme Logistics Inc.",
        loss_date="2026-03-14",
        loss_type="vehicle_collision",
        description="Tractor-trailer rollover on I-40 near Amarillo, TX.",
        severity_indicators=["bodily_injury", "high_value_cargo", "third_party"],
        needs_clarification=False,
    )
    coverage = CoverageDecision(
        covered=True,
        policy_in_force=True,
        exclusions_triggered=[],
        reasoning="Policy in force on loss date; loss type within commercial auto scope.",
        confidence=0.92,
    )
    severity = SeverityAssessment(
        severity="high",
        rationale="Bodily injury with hospitalisation + $480k cargo total loss + third party.",
        indicators=["hospitalisation", "cargo_total_loss", "multi_party"],
        confidence=0.87,
    )
    recommendation = TriageRecommendation(
        recommended_action="route_to_specialist",
        specialist_team="Casualty - North American Trucking",
        reasoning="Severity threshold breached; reinsurer notification required.",
        confidence=0.87,
    )
    trace = [
        AgentTrace(
            agent_name="intake",
            started_at_iso="2026-05-12T10:00:00Z",
            finished_at_iso="2026-05-12T10:00:01Z",
            input_summary="Raw FNOL text (412 chars)",
            output_summary="Parsed ClaimIntake for MM-PL-44721",
            tokens_in=420,
            tokens_out=180,
        ),
    ]
    return TriageState(
        raw_fnol="Tractor-trailer rollover on I-40 near Amarillo, TX. Driver hospitalised.",
        intake=intake,
        coverage=coverage,
        severity=severity,
        recommendation=recommendation,
        trace=trace,
    )


def test_fully_populated_state_fields_accessible():
    state = _fully_populated_state()

    assert state.raw_fnol.startswith("Tractor-trailer")
    assert state.intake is not None
    assert state.intake.policy_number == "MM-PL-44721"
    assert state.intake.severity_indicators == ["bodily_injury", "high_value_cargo", "third_party"]
    assert state.intake.needs_clarification is False
    assert state.coverage is not None
    assert state.coverage.covered is True
    assert state.coverage.policy_in_force is True
    assert state.coverage.exclusions_triggered == []
    assert state.coverage.confidence == 0.92
    assert state.severity is not None
    assert state.severity.severity == "high"
    assert state.severity.indicators == ["hospitalisation", "cargo_total_loss", "multi_party"]
    assert state.recommendation is not None
    assert state.recommendation.recommended_action == "route_to_specialist"
    assert state.recommendation.specialist_team == "Casualty - North American Trucking"
    assert state.recommendation.confidence == 0.87
    assert len(state.trace) == 1
    assert state.trace[0].agent_name == "intake"
    assert state.trace[0].tokens_in == 420


def test_state_roundtrips_through_json():
    state = _fully_populated_state()

    serialised = state.model_dump_json()
    parsed = TriageState.model_validate_json(serialised)

    assert parsed == state


def test_coverage_decision_rejects_out_of_range_confidence():
    with pytest.raises(ValidationError):
        CoverageDecision(
            covered=True,
            policy_in_force=True,
            exclusions_triggered=[],
            reasoning="any",
            confidence=1.5,
        )
