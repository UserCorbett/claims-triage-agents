"""Command-line entry point for the claims triage system.

Usage::

    python -m claims_triage path/to/fnol.json
    claims-triage path/to/fnol.json

The input file must be JSON. If it contains a top-level ``raw_fnol`` string,
that string is passed straight to the triage pipeline. Otherwise the whole
JSON document is serialised back to a string and used as the raw FNOL.
"""

import json
import sys
from pathlib import Path

from claims_triage.graph import triage
from claims_triage.logging_config import configure_logging

configure_logging()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: claims-triage <path-to-fnol.json>", file=sys.stderr)
        return 1

    fnol_path = Path(sys.argv[1])
    if not fnol_path.is_file():
        print(f"Error: file not found: {fnol_path}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(fnol_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {fnol_path}: {exc}", file=sys.stderr)
        return 1

    if isinstance(payload, dict) and "raw_fnol" in payload:
        raw_fnol = payload["raw_fnol"]
        if not isinstance(raw_fnol, str):
            print("Error: 'raw_fnol' must be a string", file=sys.stderr)
            return 1
    else:
        raw_fnol = json.dumps(payload, ensure_ascii=False)

    try:
        result = triage(raw_fnol)
    except Exception as exc:
        print(f"Error: triage failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
