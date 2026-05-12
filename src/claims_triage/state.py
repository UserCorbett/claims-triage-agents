"""Pydantic state models for the FNOL triage pipeline.

A single ``TriageState`` flows through the LangGraph state machine; each agent
reads the upstream fields it needs and writes its own output back. Every agent
output carries a ``confidence`` score so the graph can route low-confidence
results to a human-review path.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ClaimIntake(BaseModel):
    """Structured representation of a raw FNOL.

    Populated by the intake agent as the first step of the pipeline. Captures
    the bare facts of the claim plus a free-text list of indicators that may
    feed the later severity assessment. ``needs_clarification`` is set when
    critical fields are missing or ambiguous rather than fabricated.
    """

    policy_number: str
    claimant: str
    loss_date: str
    loss_type: str
    description: str
    severity_indicators: list[str] = Field(default_factory=list)
    needs_clarification: bool = False


class CoverageDecision(BaseModel):
    """Outcome of the coverage check.

    Populated by the coverage agent after intake. Combines a boolean coverage
    determination with the policy-in-force check, any exclusions that were
    triggered, and the reasoning behind the decision. The graph uses
    ``covered`` to decide whether to run the severity step or skip straight to
    recommendation.
    """

    covered: bool
    policy_in_force: bool
    exclusions_triggered: list[str] = Field(default_factory=list)
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class SeverityAssessment(BaseModel):
    """Severity rating for a covered claim.

    Populated by the severity agent when ``CoverageDecision.covered`` is true;
    skipped otherwise. The ``indicators`` list makes the rating auditable —
    each entry is a concrete fact from the FNOL that contributed to the
    rating.
    """

    severity: Literal["low", "medium", "high"]
    rationale: str
    indicators: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class TriageRecommendation(BaseModel):
    """Final triage decision returned to the caller.

    Populated by the recommendation agent as the last step of the pipeline.
    Synthesises all upstream state into an action and (where applicable) a
    specialist team assignment. ``specialist_team`` is ``None`` for actions
    that don't route to a team, e.g. ``decline_with_explanation`` or
    ``request_more_info``.
    """

    recommended_action: Literal[
        "route_to_specialist",
        "request_more_info",
        "fast_track",
        "decline_with_explanation",
    ]
    specialist_team: str | None = None
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class AgentTrace(BaseModel):
    """Per-agent observability record.

    Emitted at each node and appended to ``TriageState.trace`` so the full
    pipeline run is reconstructible from the final state. Timestamps are
    ISO-8601 strings; token counts come from the model response.
    """

    agent_name: str
    started_at_iso: str
    finished_at_iso: str
    input_summary: str
    output_summary: str
    tokens_in: int
    tokens_out: int


class TriageState(BaseModel):
    """Shared state passed between LangGraph nodes.

    Starts populated only with ``raw_fnol``; each agent fills in its own field
    as the graph executes. ``trace`` accumulates one ``AgentTrace`` per node
    visited. Nothing is ever overwritten — the final state is a complete
    record of the pipeline run.
    """

    raw_fnol: str
    intake: ClaimIntake | None = None
    coverage: CoverageDecision | None = None
    severity: SeverityAssessment | None = None
    recommendation: TriageRecommendation | None = None
    trace: list[AgentTrace] = Field(default_factory=list)
