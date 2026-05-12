"""Tests for the synthetic policy library."""

from datetime import date

from claims_triage.policies import get_policy


def test_get_policy_returns_acme_logistics():
    policy = get_policy("MM-PL-44721")

    assert policy is not None
    assert policy.insured_name == "Acme Logistics Inc."
    assert policy.line_of_business == "commercial_auto"
    assert policy.aggregate_limit == 5_000_000.0
    assert "third_party_bodily_injury" in policy.covered_perils


def test_get_policy_returns_none_for_unknown_number():
    assert get_policy("DOES-NOT-EXIST") is None


def test_expired_policy_expiry_date_is_before_today():
    expired = get_policy("MM-GL-77815")

    assert expired is not None
    assert expired.expiry_date < date.today()
