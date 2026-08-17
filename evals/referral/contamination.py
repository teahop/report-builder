"""Contamination guard helpers for referral evals.

Held-back final reports under data/approved-anonymized/example-reports/
must never enter prompt construction, context construction, or expectations.
"""

from __future__ import annotations

from pathlib import Path


def refuse_example_reports(path: Path | str) -> Path:
    resolved = Path(path).resolve()
    if "example-reports" in resolved.parts:
        raise RuntimeError(
            "Referral evals refuse paths under example-reports/: "
            f"{resolved}"
        )
    return resolved
