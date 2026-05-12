"""LangChain agents for the FNOL triage pipeline.

Each agent is a function that takes a ``TriageState``, makes one structured LLM
call, and returns a new state with its own field populated plus an
``AgentTrace`` appended.
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from claims_triage.policies import get_policy
from claims_triage.state import (
    AgentTrace,
    ClaimIntake,
    CoverageDecision,
    SeverityAssessment,
    TriageRecommendation,
    TriageState,
)

load_dotenv()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

_llm = ChatAnthropic(model=CLAUDE_MODEL)


INTAKE_SYSTEM_PROMPT = """You are the intake agent in an insurance claims triage system. You are given the raw text of a first-notification-of-loss (FNOL) — the message an insurer receives when a new claim is opened. Your job is to extract structured fields from that text.

Extract these fields:
- policy_number: the policy number referenced. If not present, return "UNKNOWN".
- claimant: the named insured or claimant party. If not clearly identified, return "UNKNOWN".
- loss_date: the date of loss in YYYY-MM-DD format. If only partial date information is given, return your best inference and flag needs_clarification=True.
- loss_type: a short phrase categorising the loss (e.g. "vehicle collision", "property fire", "third-party injury", "cargo damage"). Use plain language.
- description: a one-sentence summary of what happened.
- severity_indicators: a list of short factual indicators in the FNOL that point to the claim being serious. Examples: "bodily injury", "hospitalisation", "fatality", "high-value cargo", "third-party involvement", "regulatory exposure", "multi-jurisdictional". Only include indicators that are actually evidenced in the FNOL text — do not invent.
- needs_clarification: True if critical fields (policy number, claimant, loss date, or a coherent description) are missing or ambiguous enough that human review is needed before proceeding. False otherwise.

Use British English spelling and conventions in all text fields (e.g. 'hospitalised' not 'hospitalized', 'organisation' not 'organization').

Be conservative. If something isn't in the text, do not infer it from general knowledge. Mark it UNKNOWN and let downstream agents handle it."""


def intake_agent(state: TriageState) -> TriageState:
    """Extract a structured ``ClaimIntake`` from ``state.raw_fnol``."""
    started_at = datetime.now(timezone.utc).isoformat()

    structured_llm = _llm.with_structured_output(ClaimIntake, include_raw=True)
    response = structured_llm.invoke(
        [
            ("system", INTAKE_SYSTEM_PROMPT),
            ("human", state.raw_fnol),
        ]
    )

    parsed: ClaimIntake = response["parsed"]
    raw_message = response["raw"]
    usage = getattr(raw_message, "usage_metadata", None) or {}
    tokens_in = int(usage.get("input_tokens", 0) or 0)
    tokens_out = int(usage.get("output_tokens", 0) or 0)

    finished_at = datetime.now(timezone.utc).isoformat()

    trace_entry = AgentTrace(
        agent_name="intake",
        started_at_iso=started_at,
        finished_at_iso=finished_at,
        input_summary=state.raw_fnol[:200],
        output_summary=f"Parsed claim for {parsed.claimant}, loss type: {parsed.loss_type}",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    return state.model_copy(update={"intake": parsed, "trace": [*state.trace, trace_entry]})


COVERAGE_SYSTEM_PROMPT = """You are the coverage agent in an insurance claims triage system. You are given a structured claim intake and the relevant insurance policy. Your job is to decide whether the loss is covered under the policy, and explain your reasoning.

Decide on these fields:
- covered: True if the loss type is plausibly within the policy's covered_perils AND no exclusion clearly applies AND the policy was in force on the loss date. False otherwise.
- policy_in_force: True if the loss_date falls within the policy's effective_date and expiry_date (inclusive). False otherwise.
- exclusions_triggered: a list of specific exclusions from the policy that you judge apply to this loss. Only include exclusions you can defend from the facts in the claim. Empty list if none apply.
- reasoning: a concise paragraph (2-4 sentences) explaining your decision. Reference specific covered perils, specific exclusions, and the policy_in_force status. Plain English, no legalese.
- confidence: a float between 0 and 1 representing how confident you are in your decision. Use 0.9+ for clear-cut cases, 0.6-0.8 for cases that turn on judgement, below 0.6 only if you genuinely can't tell.

Be conservative. If you genuinely cannot tell whether something is covered, set covered=False, lower your confidence, and explain in reasoning. Do not invent policy terms. Use British English spelling and conventions."""


def coverage_agent(state: TriageState) -> TriageState:
    """Decide whether ``state.intake`` is covered by its referenced policy."""
    assert state.intake is not None, "coverage_agent requires state.intake to be populated"
    started_at = datetime.now(timezone.utc).isoformat()
    policy = get_policy(state.intake.policy_number)

    if policy is None:
        decision = CoverageDecision(
            covered=False,
            policy_in_force=False,
            exclusions_triggered=[],
            reasoning="Policy not found in records.",
            confidence=1.0,
        )
        tokens_in = 0
        tokens_out = 0
    else:
        human_message = (
            f"Claim intake (JSON):\n{state.intake.model_dump_json(indent=2)}\n\n"
            f"Policy (JSON):\n{policy.model_dump_json(indent=2)}"
        )
        structured_llm = _llm.with_structured_output(CoverageDecision, include_raw=True)
        response = structured_llm.invoke(
            [
                ("system", COVERAGE_SYSTEM_PROMPT),
                ("human", human_message),
            ]
        )
        decision = response["parsed"]
        raw_message = response["raw"]
        usage = getattr(raw_message, "usage_metadata", None) or {}
        tokens_in = int(usage.get("input_tokens", 0) or 0)
        tokens_out = int(usage.get("output_tokens", 0) or 0)

    finished_at = datetime.now(timezone.utc).isoformat()

    trace_entry = AgentTrace(
        agent_name="coverage",
        started_at_iso=started_at,
        finished_at_iso=finished_at,
        input_summary=f"Intake for policy {state.intake.policy_number}",
        output_summary=f"Covered: {decision.covered}, exclusions: {len(decision.exclusions_triggered)}",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    return state.model_copy(update={"coverage": decision, "trace": [*state.trace, trace_entry]})


SEVERITY_SYSTEM_PROMPT = """You are the severity agent in an insurance claims triage system. You are given a structured claim intake and the coverage decision (which has already determined the claim is covered). Your job is to assess how serious this claim is — low, medium, or high severity — so it can be routed to the right team.

Decide on these fields:
- severity: one of "low", "medium", or "high".
- rationale: a concise paragraph (2-4 sentences) explaining your assessment. Reference specific facts from the claim. Plain English.
- indicators: a list of short factual indicators from the claim that drove your assessment. Examples: "bodily injury with hospitalisation", "third-party involvement", "cargo value over USD 250k", "potential regulatory exposure", "multi-jurisdictional", "minor property damage only". Each indicator must be defensible from the claim text.
- confidence: a float between 0 and 1 representing how confident you are in the severity rating.

Use these rough thresholds as guidance, but apply judgement:
- HIGH: bodily injury requiring hospitalisation, fatality, financial loss above USD 250,000, third-party claims with significant exposure, regulatory or environmental implications, multi-party litigation potential.
- MEDIUM: bodily injury without hospitalisation, financial loss between USD 50,000 and USD 250,000, single-party claims with moderate complexity, third-party damage without injury.
- LOW: property damage only under USD 50,000, no injuries, no third parties, no regulatory exposure, straightforward facts.

If a claim has indicators that span thresholds, escalate to the higher severity — never under-call. It is cheaper for an insurer to over-triage than under-triage. Use British English spelling."""


def severity_agent(state: TriageState) -> TriageState:
    """Assess severity given ``state.intake`` and ``state.coverage``."""
    assert state.intake is not None, "severity_agent requires state.intake"
    assert state.coverage is not None, "severity_agent requires state.coverage"
    started_at = datetime.now(timezone.utc).isoformat()

    human_message = (
        f"Claim intake (JSON):\n{state.intake.model_dump_json(indent=2)}\n\n"
        f"Coverage decision (JSON):\n{state.coverage.model_dump_json(indent=2)}"
    )
    structured_llm = _llm.with_structured_output(SeverityAssessment, include_raw=True)
    response = structured_llm.invoke(
        [
            ("system", SEVERITY_SYSTEM_PROMPT),
            ("human", human_message),
        ]
    )
    assessment = response["parsed"]
    raw_message = response["raw"]
    usage = getattr(raw_message, "usage_metadata", None) or {}
    tokens_in = int(usage.get("input_tokens", 0) or 0)
    tokens_out = int(usage.get("output_tokens", 0) or 0)

    finished_at = datetime.now(timezone.utc).isoformat()

    trace_entry = AgentTrace(
        agent_name="severity",
        started_at_iso=started_at,
        finished_at_iso=finished_at,
        input_summary=f"Intake + coverage for policy {state.intake.policy_number}",
        output_summary=f"Severity: {assessment.severity} ({len(assessment.indicators)} indicators)",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    return state.model_copy(update={"severity": assessment, "trace": [*state.trace, trace_entry]})


RECOMMENDATION_SYSTEM_PROMPT = """You are the recommendation agent in an insurance claims triage system. You are given the upstream outputs from prior agents — claim intake, coverage decision, and (when applicable) severity assessment. Your job is to recommend the next action for this claim.

Decide on these fields:
- recommended_action: one of "route_to_specialist", "request_more_info", "fast_track", "decline_with_explanation".
- specialist_team: the name of the team this should be routed to, or null if not routing to a specialist. Use team names like: "Casualty - North American Trucking", "Property - International", "Liability - Professional", "Casualty - UK Motor", "Property - UK Commercial", "General - Low Severity Desk". Choose the team that best matches the line of business, jurisdiction, and severity.
- reasoning: a concise paragraph (3-5 sentences) explaining your recommendation. Reference the coverage decision, severity (if available), and any factors that drove the routing decision.
- confidence: a float between 0 and 1 representing your confidence.

Action guidance:
- "route_to_specialist": Use for medium and high severity claims that are covered, where a specialist team needs to take ownership. Always specify a specialist_team.
- "fast_track": Use for low-severity, covered claims with no third-party complexity — these can go to the General - Low Severity Desk for streamlined handling.
- "request_more_info": Use when intake's needs_clarification flag is True, or when critical facts are missing that would materially change the recommendation. The reasoning should specify what's missing.
- "decline_with_explanation": Use when coverage is False or the policy was not in force at the loss date. Always explain to the claimant in plain terms why coverage doesn't apply.

Use British English spelling. Be specific about the team — generic recommendations are not useful."""


def recommendation_agent(state: TriageState) -> TriageState:
    """Recommend the next action given all upstream agent outputs."""
    assert state.intake is not None, "recommendation_agent requires state.intake"
    assert state.coverage is not None, "recommendation_agent requires state.coverage"
    started_at = datetime.now(timezone.utc).isoformat()

    if state.severity is not None:
        severity_block = state.severity.model_dump_json(indent=2)
    else:
        severity_block = "Not assessed — coverage was negative or skipped"

    human_message = (
        f"Claim intake (JSON):\n{state.intake.model_dump_json(indent=2)}\n\n"
        f"Coverage decision (JSON):\n{state.coverage.model_dump_json(indent=2)}\n\n"
        f"Severity assessment:\n{severity_block}"
    )
    structured_llm = _llm.with_structured_output(TriageRecommendation, include_raw=True)
    response = structured_llm.invoke(
        [
            ("system", RECOMMENDATION_SYSTEM_PROMPT),
            ("human", human_message),
        ]
    )
    recommendation = response["parsed"]
    raw_message = response["raw"]
    usage = getattr(raw_message, "usage_metadata", None) or {}
    tokens_in = int(usage.get("input_tokens", 0) or 0)
    tokens_out = int(usage.get("output_tokens", 0) or 0)

    finished_at = datetime.now(timezone.utc).isoformat()

    trace_entry = AgentTrace(
        agent_name="recommendation",
        started_at_iso=started_at,
        finished_at_iso=finished_at,
        input_summary=f"All upstream for policy {state.intake.policy_number}",
        output_summary=(
            f"Action: {recommendation.recommended_action}, "
            f"team: {recommendation.specialist_team or 'N/A'}"
        ),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    return state.model_copy(
        update={"recommendation": recommendation, "trace": [*state.trace, trace_entry]}
    )
