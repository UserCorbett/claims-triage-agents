"""Synthetic policy library for the coverage agent.

Reference data, not state — these are the policies the coverage agent looks
up to decide whether a claim is covered. In production this would be a query
against a policy admin system; here it's an in-memory dict for the demo.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class Policy(BaseModel):
    """A single insurance policy record.

    The coverage agent matches an incoming claim against one of these by
    policy_number, then checks effective/expiry dates, line of business, and
    the covered_perils / exclusions lists to decide coverage.
    """

    policy_number: str
    insured_name: str
    effective_date: date
    expiry_date: date
    line_of_business: Literal["commercial_auto", "property", "general_liability"]
    covered_perils: list[str]
    exclusions: list[str]
    aggregate_limit: float


POLICIES: dict[str, Policy] = {
    "MM-PL-44721": Policy(
        policy_number="MM-PL-44721",
        insured_name="Acme Logistics Inc.",
        effective_date=date(2025, 1, 1),
        expiry_date=date(2026, 12, 31),
        line_of_business="commercial_auto",
        covered_perils=[
            "collision",
            "rollover",
            "cargo_loss",
            "third_party_bodily_injury",
            "third_party_property_damage",
        ],
        exclusions=[
            "intentional_acts",
            "racing",
            "use_outside_north_america",
        ],
        aggregate_limit=5_000_000.0,
    ),
    "MM-PR-10234": Policy(
        policy_number="MM-PR-10234",
        insured_name="Thames Riverside Manufacturing Ltd.",
        effective_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        line_of_business="property",
        covered_perils=[
            "fire",
            "theft",
            "storm",
            "escape_of_water",
            "impact",
        ],
        exclusions=[
            "flood",
            "war_and_terrorism",
            "nuclear",
            "wear_and_tear",
        ],
        aggregate_limit=10_000_000.0,
    ),
    "MM-GL-77815": Policy(
        policy_number="MM-GL-77815",
        insured_name="Riverbend Consulting LLC",
        effective_date=date(2023, 7, 1),
        expiry_date=date(2024, 6, 30),
        line_of_business="general_liability",
        covered_perils=[
            "bodily_injury",
            "property_damage",
            "advertising_injury",
        ],
        exclusions=[
            "professional_services",
            "pollution",
            "asbestos",
        ],
        aggregate_limit=2_000_000.0,
    ),
    "MM-GL-22099": Policy(
        policy_number="MM-GL-22099",
        insured_name="Borough Bakehouse Ltd.",
        effective_date=date(2026, 3, 1),
        expiry_date=date(2027, 2, 28),
        line_of_business="general_liability",
        covered_perils=[
            "bodily_injury",
            "property_damage",
            "products_liability",
        ],
        exclusions=[
            "professional_services",
            "pollution",
        ],
        aggregate_limit=100_000.0,
    ),
    "MM-PL-58302": Policy(
        policy_number="MM-PL-58302",
        insured_name="Citywide Couriers Ltd.",
        effective_date=date(2025, 9, 1),
        expiry_date=date(2026, 8, 31),
        line_of_business="commercial_auto",
        covered_perils=[
            "collision",
            "theft",
            "third_party_bodily_injury",
            "third_party_property_damage",
        ],
        exclusions=[
            "intentional_acts",
            "racing",
            "carriage_of_dangerous_goods",
        ],
        aggregate_limit=750_000.0,
    ),
}


def get_policy(policy_number: str) -> Policy | None:
    """Return the policy with this number, or None if it doesn't exist."""
    return POLICIES.get(policy_number)
