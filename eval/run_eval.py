"""Run the eval set and print a pass/fail report.

Loads ``eval/eval_set.yaml``, runs the full triage pipeline on each fixture,
checks the three headline assertions per case (coverage decision, severity,
recommended action), and prints a readable table plus a summary.

Exits 0 if every case passes, 1 otherwise. Intended to be run by a human as
well as CI — the output should be self-explanatory.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from claims_triage.graph import triage


@dataclass
class CaseResult:
    fixture: str
    coverage_pass: bool
    severity_pass: bool
    action_pass: bool
    expected: dict
    actual: dict

    @property
    def overall_pass(self) -> bool:
        return self.coverage_pass and self.severity_pass and self.action_pass


def _run_case(repo_root: Path, case: dict) -> CaseResult:
    fixture_path = repo_root / case["fixture"]
    expected = case["expected"]

    raw_fnol = json.loads(fixture_path.read_text(encoding="utf-8"))["raw_fnol"]
    state = triage(raw_fnol)

    actual_coverage = state.coverage.covered if state.coverage else None
    actual_severity = state.severity.severity if state.severity else None
    actual_action = state.recommendation.recommended_action if state.recommendation else None

    return CaseResult(
        fixture=case["fixture"],
        coverage_pass=actual_coverage == expected["coverage_covered"],
        severity_pass=actual_severity == expected["severity"],
        action_pass=actual_action == expected["recommended_action"],
        expected=expected,
        actual={
            "coverage_covered": actual_coverage,
            "severity": actual_severity,
            "recommended_action": actual_action,
        },
    )


def _cell(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _print_report(results: list[CaseResult]) -> None:
    fixture_col_width = max(len(r.fixture) for r in results) + 2
    headers = ["Fixture", "Coverage", "Severity", "Action", "Overall"]
    widths = [fixture_col_width, 10, 10, 10, 10]

    def _row(cells: list[str]) -> str:
        return " | ".join(c.ljust(w) for c, w in zip(cells, widths))

    print(_row(headers))
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))
    for r in results:
        print(_row([
            r.fixture,
            _cell(r.coverage_pass),
            _cell(r.severity_pass),
            _cell(r.action_pass),
            _cell(r.overall_pass),
        ]))

    failures = [r for r in results if not r.overall_pass]
    if failures:
        print()
        print("Failure detail:")
        for r in failures:
            print(f"  {r.fixture}")
            for key in ("coverage_covered", "severity", "recommended_action"):
                if r.expected[key] != r.actual[key]:
                    print(f"    {key}: expected {r.expected[key]!r}, got {r.actual[key]!r}")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    eval_set = yaml.safe_load((repo_root / "eval" / "eval_set.yaml").read_text(encoding="utf-8"))
    cases = eval_set["cases"]

    results = [_run_case(repo_root, c) for c in cases]
    _print_report(results)

    total = len(results)
    cases_passed = sum(1 for r in results if r.overall_pass)
    assertions_passed = sum(
        int(r.coverage_pass) + int(r.severity_pass) + int(r.action_pass) for r in results
    )
    assertions_failed = (total * 3) - assertions_passed

    print()
    print(
        f"{cases_passed} of {total} cases passed "
        f"({assertions_passed} assertions PASS, {assertions_failed} FAIL)"
    )

    return 0 if cases_passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
