"""Recall-only voice gate: load the compiled store from disk and score a draft.

This process does not compile the store, does not read DECISIONS.md, and does
not take rule text as input. The draft is a JSON file path. The only path
from rule to verdict is voice_store.json on disk.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schemas import DraftProseOutput
from voice_store import STORE_PATH, evaluate_voice_gates, voice_store_sha


def score_draft_path(draft_path: Path, *, store_path: Path | None = None) -> None:
    output = DraftProseOutput.model_validate_json(draft_path.read_text(encoding="utf-8"))
    report = evaluate_voice_gates(output, store_path=store_path)
    sha = report.store_sha or voice_store_sha(store_path)
    print(f"store_path={store_path or STORE_PATH}")
    print(f"store_sha={sha}")
    print(f"draft_path={draft_path}")
    fails = [c for c in report.checks if c.result == "fail"]
    if not fails:
        print("failures=0")
        return
    print(f"failures={len(fails)}")
    for check in fails:
        print(f"FAIL {check.id}")
        print(f"  span: {check.span}")
        print(f"  summary: {check.summary}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Score a draft against the compiled voice store on disk. "
            "Pass a JSON path; do not pass rule text."
        )
    )
    parser.add_argument(
        "draft",
        help="Path to a DraftProseOutput JSON file (the tempted draft, not a rule).",
    )
    args = parser.parse_args(argv)
    draft_path = Path(args.draft)
    if not draft_path.is_file():
        print(f"draft not found: {draft_path}", file=sys.stderr)
        return 2
    score_draft_path(draft_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
