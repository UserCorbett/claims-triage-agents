"""LangGraph orchestration for the FNOL triage pipeline.

The graph is a ``StateGraph`` keyed on ``TriageState``. The four agents are
wired as nodes; a conditional edge after the coverage node skips severity for
claims that aren't covered.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from claims_triage.agents import (
    coverage_agent,
    intake_agent,
    recommendation_agent,
    severity_agent,
)
from claims_triage.state import TriageState


def route_after_coverage(state: TriageState) -> str:
    """Send covered claims through severity, uncovered ones straight to recommendation."""
    if state.coverage and state.coverage.covered:
        return "severity"
    return "recommendation"


def build_graph() -> Any:
    """Build and compile the FNOL triage StateGraph."""
    graph = StateGraph(TriageState)
    graph.add_node("intake", intake_agent)
    graph.add_node("coverage", coverage_agent)
    graph.add_node("severity", severity_agent)
    graph.add_node("recommendation", recommendation_agent)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "coverage")
    graph.add_conditional_edges(
        "coverage",
        route_after_coverage,
        {"severity": "severity", "recommendation": "recommendation"},
    )
    graph.add_edge("severity", "recommendation")
    graph.add_edge("recommendation", END)

    return graph.compile()


_GRAPH = build_graph()


def triage(raw_fnol: str) -> TriageState:
    """Run the full triage pipeline on a raw FNOL string."""
    initial_state = TriageState(raw_fnol=raw_fnol)
    result = _GRAPH.invoke(initial_state)
    return TriageState(**result) if isinstance(result, dict) else result
