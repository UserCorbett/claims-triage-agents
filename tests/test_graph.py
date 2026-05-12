"""Integration tests for the LangGraph orchestration."""

import pytest

from claims_triage.graph import triage


@pytest.mark.integration
def test_graph_runs_full_pipeline_on_high_severity_claim():
    raw_fnol = (
        "Policy MM-PL-44721. Tractor-trailer rollover on I-40 near Amarillo, TX "
        "on 14 March 2026. Driver hospitalised with suspected concussion. "
        "Cargo (electronics, est. value $480k) total loss. "
        "Second vehicle involved, no injuries reported. Police report filed. "
        "Claimant: Acme Logistics Inc."
    )
    result = triage(raw_fnol)

    assert result.intake is not None
    assert result.coverage is not None
    assert result.severity is not None
    assert result.recommendation is not None

    assert len(result.trace) == 4
    agent_names_in_order = [t.agent_name for t in result.trace]
    assert agent_names_in_order == ["intake", "coverage", "severity", "recommendation"]

    assert result.severity.severity == "high"
    assert result.recommendation.recommended_action == "route_to_specialist"


@pytest.mark.integration
def test_graph_skips_severity_when_coverage_denied():
    raw_fnol = (
        "Policy DOES-NOT-EXIST. Minor collision in car park on 1 May 2026. "
        "No injuries. Claimant: Test Company Ltd."
    )
    result = triage(raw_fnol)

    assert result.severity is None

    assert len(result.trace) == 3
    agent_names = [t.agent_name for t in result.trace]
    assert "severity" not in agent_names

    assert result.recommendation.recommended_action == "decline_with_explanation"
