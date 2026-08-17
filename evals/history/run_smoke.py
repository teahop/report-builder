"""One History-package smoke from cached fixture_001 — hard stop after a single run."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from dotenv import load_dotenv

load_dotenv(_WEEK1 / ".env")

from conflicts import detect_disagreements_from_ledger
from history_draft import draft_history_package, history_policy_hash
from history_langfuse import flush_langfuse
from history_schemas import HistoryDraftRequest
from history_structure import structure_spec_hash
from langfuse import observe
from evals.panel_checks import score_history_record
from provider import BASTION_MODEL, DRAFT_TEMPERATURE, ModelProvider
from retries import VALIDATION_RETRY_ATTEMPTS, run_with_validation_retries
from schemas import Ledger

_DIR = Path(__file__).resolve().parent
_TRACES = _DIR / "traces"
_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"


def _load_ledger() -> Ledger:
    raw = json.loads(_CACHE.read_text(encoding="utf-8"))
    return Ledger.model_validate(raw["ledger"] if "ledger" in raw else raw)


def _human_readable(package, rendered: str, review_items: list | None = None) -> str:
    lines = [
        f"structure_spec_id: {package.structure_spec_id}",
        f"structure_spec_hash: {package.structure_spec_hash}",
        f"policy_hash: {package.policy_hash}",
        f"voice_store_sha: {getattr(package, 'voice_store_sha', '')}",
        "",
        "## Assembled sections / blocks",
    ]
    for section in package.sections:
        lines.append(
            f"- {section.section_key} ({section.display_label}) "
            f"populated={section.section_populated}"
        )
        for block in section.blocks:
            lines.append(
                f"  - {block.block_key} / {block.display_label} "
                f"kind={block.kind} fact_ids={len(block.fact_ids)}"
            )
    lines.append("")
    lines.append("## Input-schema gaps")
    if package.input_schema_gaps:
        lines.extend(f"- {g}" for g in package.input_schema_gaps)
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Reuse records (fact appears across sections)")
    by_fact: dict[str, list] = {}
    for r in package.reuse_records:
        by_fact.setdefault(r.fact_id, []).append(r)
    multi = {fid: rows for fid, rows in by_fact.items() if len(rows) > 1}
    if not multi:
        lines.append("- (no multi-section reuse in this run)")
    else:
        for fid, rows in sorted(multi.items()):
            detail = "; ".join(f"{r.section_key}/{r.block_key} ({r.purpose})" for r in rows)
            lines.append(f"- {fid}: {detail}")
    lines.append("")
    lines.append("## Review queue")
    items = list(review_items or [])
    if not items:
        lines.append("- (none)")
    else:
        for item in items:
            lines.append(f"- {item.kind}: {item.summary}")
    lines.append("")
    lines.append("## Rendered History")
    lines.append(rendered)
    return "\n".join(lines)


@observe(name="eval.history.smoke.fixture_001")
def _run_draft(provider: ModelProvider, body: HistoryDraftRequest):
    return run_with_validation_retries(
        lambda _attempt: draft_history_package(provider, body),
        max_attempts=VALIDATION_RETRY_ATTEMPTS,
        failure_prefix="History smoke failed validation after retry",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("openai", "bastion"),
        default="openai",
        help="Drafting backend. Ledger stays the cached fixture_001 parent.",
    )
    args = parser.parse_args(argv)

    _TRACES.mkdir(parents=True, exist_ok=True)
    if not _CACHE.is_file():
        print(f"Missing cached ledger: {_CACHE}", file=sys.stderr)
        return 2

    ledger = _load_ledger()
    conflicts, variance, *_ = detect_disagreements_from_ledger(ledger)
    if args.provider == "bastion":
        provider = ModelProvider(backend="bastion")
        model = BASTION_MODEL
    else:
        provider = ModelProvider()
        model = "gpt-4o-mini"
    body = HistoryDraftRequest(
        confirm_synthetic=True,
        ledger=ledger,
        conflicts=conflicts,
        variance=variance,
        structure_spec_id="provisional_tj_v1",
        model=model,
        entailment_model=model,
        # Smoke focuses on assembled structure/prose; entailment covered by unit path.
        skip_entailment=True,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    start = time.perf_counter()
    try:
        response = _run_draft(provider, body)
    except Exception as exc:
        flush_langfuse()
        latency_ms = int((time.perf_counter() - start) * 1000)
        trace_path = _TRACES / f"smoke-{stamp}.jsonl"
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "fixture_id": "fixture_001",
            "structure_spec_id": "provisional_tj_v1",
            "structure_spec_hash": structure_spec_hash("provisional_tj_v1"),
            "policy_hash": history_policy_hash(),
            "provider": args.provider,
            "model": model,
            "temperature": DRAFT_TEMPERATURE,
            "status": "validation_failed",
            "error": str(exc),
            "latency_ms": latency_ms,
        }
        trace_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        print(f"FAILED: {exc}")
        print(f"trace={trace_path}")
        return 1

    flush_langfuse()
    latency_ms = int((time.perf_counter() - start) * 1000)
    response.latency_ms = latency_ms
    package = response.package
    readable = _human_readable(
        package, response.rendered_prose, response.review.items
    )

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "fixture_id": "fixture_001",
        "structure_spec_id": package.structure_spec_id,
        "structure_spec_hash": package.structure_spec_hash,
        "policy_hash": package.policy_hash,
        "prompt_hash": response.prompt_hash,
        "voice_store_sha": getattr(response, "voice_store_sha", ""),
        "voice_gate": getattr(response, "voice_gate", None),
        "provider": args.provider,
        "model": response.model,
        "temperature": DRAFT_TEMPERATURE,
        "status": "ok",
        "section_populated": response.section_populated,
        "tokens_used": response.tokens_used,
        "tokens_by_stage": response.tokens_by_stage,
        "latency_ms": latency_ms,
        "cost_usd": response.cost_usd,
        "trace_id": response.trace_id,
        "langfuse_url": response.langfuse_url,
        "input_schema_gaps": package.input_schema_gaps,
        "sections": [
            {
                "section_key": s.section_key,
                "display_label": s.display_label,
                "purpose": s.purpose,
                "section_populated": s.section_populated,
                "empty_reason": s.empty_reason,
                "blocks": [
                    {
                        "block_key": b.block_key,
                        "display_label": b.display_label,
                        "kind": b.kind,
                        "fact_ids": b.fact_ids,
                    }
                    for b in s.blocks
                ],
                "prose": s.draft_output.prose if s.draft_output else "",
                "statement_fact_ids": (
                    [stmt.fact_ids for stmt in s.draft_output.statements]
                    if s.draft_output
                    else []
                ),
            }
            for s in package.sections
        ],
        "reuse_records": [r.model_dump() for r in package.reuse_records],
        "conflicts_count": len(conflicts),
        "variance_count": len(variance),
        "rendered_prose": response.rendered_prose,
        "review": [item.model_dump() for item in response.review.items],
        "skip_entailment": True,
    }

    trace_path = _TRACES / f"smoke-{stamp}.jsonl"
    readable_path = _TRACES / f"smoke-{stamp}.md"
    trace_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    readable_path.write_text(readable, encoding="utf-8")

    print(readable)
    print()
    gate = getattr(response, "voice_gate", None) or {}
    print("Voice gate (A6/A7/A8 strip-and-measure)")
    for check in gate.get("checks") or []:
        if check.get("id") in {
            "voice.write_about_child",
            "voice.informants_distinct",
            "voice.no_meta_narration",
        }:
            print(
                f"  {check.get('section_key')}/{check.get('id')}: "
                f"{check.get('result')} — {check.get('summary')}"
                + (f" span={check.get('span')!r}" if check.get("span") else "")
            )
    print()
    print(f"trace={trace_path}")
    print(f"readable={readable_path}")
    print(f"langfuse_trace_id={response.trace_id}")
    print(f"langfuse_url={response.langfuse_url}")
    print(
        f"tokens={response.tokens_used} cost_usd={response.cost_usd} "
        f"latency_ms={latency_ms} provider={args.provider} model={response.model}"
    )
    print()
    print("TRACE checks vs 20-run baseline (opener 0/20 pass; n=20)")
    for check in score_history_record(record):
        mark = "pass" if check.passed else "fail"
        print(f"  {check.name}: {mark} — {check.detail}")
    print("HARD STOP — traced smoke only; no retune / no sweep.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
