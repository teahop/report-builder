"""3–5 live extracts of fixture_001 doc_11 + doc_13 for Groups B/D review.

Does not overwrite evals/cache/fixture_001_ledger.json.
Does not call OpenAI itself — POSTs /extract on a running app.
skip_entailment defaults true so this measures minting, not §9.3.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[4]
FIXTURE_DIR = ROOT / "fixtures" / "fixture_001"
OUT_DIR = Path(__file__).resolve().parent / "runs"

KEEPERS = (
    "anticipated_graduation_date",
    "alternative_diploma_pathway_eligibility",
    "caaspp_participation",
    "conservatorship_status",
    "peer_relationships",
    "skill_generalization",
    "parental_limitations",
)
REJECTED = ("unsafe_behaviors_at_home", "school_setting_success")
GROUP_C = ("english_learner_status", "behavior_impedes_learning", "diagnosis_list")
WATCH = KEEPERS + REJECTED + GROUP_C


def _load_packet(name: str) -> dict:
    data = json.loads((FIXTURE_DIR / name).read_text())
    return {
        "confirm_synthetic": True,
        "child": data["child"],
        "sources": data["sources"],
        "model": "gpt-4o-mini",
        "skip_entailment": True,
    }


def _facts(payload: dict) -> list[dict]:
    ledger = payload.get("ledger") or {}
    return list(ledger.get("facts") or [])


def _mark(facts: list[dict], review: list[str], name: str) -> str:
    minted = [f for f in facts if f.get("predicate") == name]
    if minted:
        sample = minted[0]
        val = repr(sample.get("value") or "")[:80]
        return f"minted n={len(minted)} id={sample.get('id')} value={val}"
    proposed = [
        f
        for f in facts
        if f.get("proposed_predicate") == name or f.get("predicate") == name
    ]
    if name in review or proposed:
        return "hatch"
    return "absent"


def _fragment(source_id: str, run: int, payload: dict) -> str:
    facts = _facts(payload)
    review = list(payload.get("predicates_for_review") or [])
    lines = [
        f"### {source_id} run {run}",
        f"latency_ms={payload.get('latency_ms')} cost_usd={payload.get('cost_usd')} "
        f"facts={len(facts)}",
        "",
        "| name | mark |",
        "|---|---|",
    ]
    for name in WATCH:
        lines.append(f"| `{name}` | {_mark(facts, review, name)} |")
    lines.append("")
    lines.append(f"`predicates_for_review`: {review}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument(
        "--sources",
        default="doc_13,doc_11",
        help="Comma-separated fixture filenames without .json (default: doc_13,doc_11)",
    )
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = OUT_DIR / stamp
    out.mkdir(parents=True, exist_ok=True)
    timeout = httpx.Timeout(600.0)
    md_parts = [f"# Groups B/D live extract {stamp}", ""]
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=timeout) as client:
        for source in [s.strip() for s in args.sources.split(",") if s.strip()]:
            body = _load_packet(f"{source}.json")
            for run in range(1, args.runs + 1):
                print(f"{source} run {run}/{args.runs} …", flush=True)
                resp = client.post("/extract", json=body)
                resp.raise_for_status()
                payload = resp.json()
                (out / f"{source}_run{run}.json").write_text(
                    json.dumps(payload, indent=2) + "\n"
                )
                md_parts.append(_fragment(source, run, payload))
    summary = out / "review_fragment.md"
    summary.write_text("\n".join(md_parts))
    print(f"wrote {summary}")


if __name__ == "__main__":
    main()
