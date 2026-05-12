"""Tests for the FNOL triage agents.

Integration tests carry the ``integration`` marker because they hit the real
Claude API and need ``ANTHROPIC_API_KEY`` in the environment.
"""

import pytest

from claims_triage.agents import (
    coverage_agent,
    intake_agent,
    recommendation_agent,
    severity_agent,
)
from claims_triage.state import (
    ClaimIntake,
    CoverageDecision,
    SeverityAssessment,
    TriageState,
)


@pytest.mark.integration
def test_intake_agent_extracts_high_severity_fnol():
    raw_fnol = (
        "Policy MM-PL-44721. Tractor-trailer rollover on I-40 near Amarillo, TX "
        "on 14 March 2026. Driver hospitalised with suspected concussion. "
        "Cargo (electronics, est. value $480k) total loss. "
        "Second vehicle involved, no injuries reported. Police report filed. "
        "Claimant: Acme Logistics Inc."
    )
    state = TriageState(raw_fnol=raw_fnol)
    result = intake_agent(state)
    assert result.intake is not None
    assert result.intake.policy_number == "MM-PL-44721"
    assert "Acme" in result.intake.claimant
    assert result.intake.loss_date == "2026-03-14"
    assert len(result.intake.severity_indicators) >= 2
    assert len(result.trace) == 1
    assert result.trace[0].agent_name == "intake"


@pytest.mark.integration
def test_coverage_agent_finds_acme_logistics_covered():
    intake = ClaimIntake(
        policy_number="MM-PL-44721",
        claimant="Acme Logistics Inc.",
        loss_date="2026-03-14",
        loss_type="tractor-trailer rollover",
        description=(
            "Tractor-trailer rollover on I-40 near Amarillo, Texas. Driver "
            "hospitalised with suspected concussion. Cargo (electronics, est. "
            "value $480k) total loss. Second vehicle involved, no injuries."
        ),
        severity_indicators=[
            "hospitalisation",
            "high-value cargo",
            "third-party involvement",
        ],
        needs_clarification=False,
    )
    state = TriageState(raw_fnol="...", intake=intake)
    result = coverage_agent(state)

    assert result.coverage is not None
    assert result.coverage.covered is True
    assert result.coverage.policy_in_force is True
    assert result.coverage.exclusions_triggered == []
    assert result.coverage.confidence >= 0.8
    assert result.trace[-1].agent_name == "coverage"


@pytest.mark.integration
def test_coverage_agent_rejects_unknown_policy():
    intake = ClaimIntake(
        policy_number="DOES-NOT-EXIST",
        claimant="Phantom Holdings Ltd.",
        loss_date="2026-03-14",
        loss_type="vehicle collision",
        description="Single-vehicle collision, minor damage.",
        severity_indicators=[],
        needs_clarification=False,
    )
    state = TriageState(raw_fnol="...", intake=intake)
    result = coverage_agent(state)

    assert result.coverage is not None
    assert result.coverage.covered is False
    assert "not found" in result.coverage.reasoning.lower()
    assert result.trace[-1].agent_name == "coverage"
    assert result.trace[-1].tokens_in == 0
    assert result.trace[-1].tokens_out == 0


@pytest.mark.integration
def test_severity_agent_rates_acme_trucking_high():
    intake = ClaimIntake(
        policy_number="MM-PL-44721",
        claimant="Acme Logistics Inc.",
        loss_date="2026-03-14",
        loss_type="tractor-trailer rollover",
        description=(
            "Tractor-trailer rollover on I-40 near Amarillo, Texas. Driver "
            "hospitalised with suspected concussion. Cargo (electronics, est. "
            "value $480k) total loss. Second vehicle involved, no injuries."
        ),
        severity_indicators=[
            "hospitalisation",
            "high-value cargo",
            "third-party involvement",
        ],
        needs_clarification=False,
    )
    coverage = CoverageDecision(
        covered=True,
        policy_in_force=True,
        exclusions_triggered=[],
        reasoning=(
            "Policy in force on loss date; loss falls within covered perils "
            "(rollover, cargo loss, collision)."
        ),
        confidence=0.95,
    )
    state = TriageState(raw_fnol="...", intake=intake, coverage=coverage)
    result = severity_agent(state)

    assert result.severity is not None
    assert result.severity.severity == "high"
    assert result.severity.confidence >= 0.8
    indicators_text = " ".join(result.severity.indicators).lower()
    assert "bodily injury" in indicators_text or "hospitalis" in indicators_text
    assert result.trace[-1].agent_name == "severity"


@pytest.mark.integration
def test_severity_agent_rates_minor_loss_low():
    intake = ClaimIntake(
        policy_number="MM-PL-44721",
        claimant="Acme Logistics Inc.",
        loss_date="2026-03-14",
        loss_type="minor vehicle collision",
        description=(
            "Minor rear-end collision in car park. No injuries. Bumper damage "
            "only, est. $1,200. No third parties involved."
        ),
        severity_indicators=[],
        needs_clarification=False,
    )
    coverage = CoverageDecision(
        covered=True,
        policy_in_force=True,
        exclusions_triggered=[],
        reasoning="Policy in force on loss date; collision is a covered peril.",
        confidence=0.95,
    )
    state = TriageState(raw_fnol="...", intake=intake, coverage=coverage)
    result = severity_agent(state)

    assert result.severity is not None
    assert result.severity.severity == "low"
    assert result.trace[-1].agent_name == "severity"


@pytest.mark.integration
def test_recommendation_for_high_severity_covered_claim_routes_to_specialist():
    intake = ClaimIntake(
        policy_number="MM-PL-44721",
        claimant="Acme Logistics Inc.",
        loss_date="2026-03-14",
        loss_type="tractor-trailer rollover",
        description=(
            "Tractor-trailer rollover on I-40 near Amarillo, Texas. Driver "
            "hospitalised with suspected concussion. Cargo (electronics, est. "
            "value $480k) total loss. Second vehicle involved, no injuries."
        ),
        severity_indicators=[
            "hospitalisation",
            "high-value cargo",
            "third-party involvement",
        ],
        needs_clarification=False,
    )
    coverage = CoverageDecision(
        covered=True,
        policy_in_force=True,
        exclusions_triggered=[],
        reasoning="Policy in force; loss falls within covered perils.",
        confidence=0.95,
    )
    severity = SeverityAssessment(
        severity="high",
        rationale=(
            "Bodily injury with hospitalisation; cargo loss over USD 250k; third-party involvement."
        ),
        indicators=[
            "bodily injury with hospitalisation",
            "cargo value exceeds USD 250,000",
            "third-party vehicle involvement",
        ],
        confidence=0.92,
    )
    state = TriageState(raw_fnol="...", intake=intake, coverage=coverage, severity=severity)
    result = recommendation_agent(state)

    assert result.recommendation is not None
    assert result.recommendation.recommended_action == "route_to_specialist"
    assert result.recommendation.specialist_team is not None
    team_lower = result.recommendation.specialist_team.lower()
    assert "trucking" in team_lower or "north american" in team_lower
    assert result.trace[-1].agent_name == "recommendation"


@pytest.mark.integration
def test_recommendation_for_low_severity_covered_claim_fast_tracks():
    intake = ClaimIntake(
        policy_number="MM-PL-44721",
        claimant="Acme Logistics Inc.",
        loss_date="2026-03-14",
        loss_type="minor vehicle collision",
        description=(
            "Minor rear-end collision in car park. No injuries. Bumper damage "
            "only, est. $1,200. No third parties involved."
        ),
        severity_indicators=[],
        needs_clarification=False,
    )
    coverage = CoverageDecision(
        covered=True,
        policy_in_force=True,
        exclusions_triggered=[],
        reasoning="Policy in force; collision within covered perils.",
        confidence=0.95,
    )
    severity = SeverityAssessment(
        severity="low",
        rationale="Property damage only, under USD 50k, no injuries, no third parties.",
        indicators=[
            "property damage only",
            "estimated loss under USD 50,000",
            "no bodily injury",
            "no third-party involvement",
        ],
        confidence=0.98,
    )
    state = TriageState(raw_fnol="...", intake=intake, coverage=coverage, severity=severity)
    result = recommendation_agent(state)

    assert result.recommendation is not None
    assert result.recommendation.recommended_action == "fast_track"
    assert result.trace[-1].agent_name == "recommendation"


@pytest.mark.integration
def test_recommendation_for_unknown_policy_declines():
    intake = ClaimIntake(
        policy_number="DOES-NOT-EXIST",
        claimant="Phantom Holdings Ltd.",
        loss_date="2026-03-14",
        loss_type="vehicle collision",
        description="Single-vehicle collision, minor damage.",
        severity_indicators=[],
        needs_clarification=False,
    )
    coverage = CoverageDecision(
        covered=False,
        policy_in_force=False,
        exclusions_triggered=[],
        reasoning="Policy not found in records.",
        confidence=1.0,
    )
    state = TriageState(raw_fnol="...", intake=intake, coverage=coverage)
    result = recommendation_agent(state)

    assert result.recommendation is not None
    assert result.recommendation.recommended_action == "decline_with_explanation"
    reasoning_lower = result.recommendation.reasoning.lower()
    assert "policy" in reasoning_lower or "coverage" in reasoning_lower
    assert result.trace[-1].agent_name == "recommendation"
