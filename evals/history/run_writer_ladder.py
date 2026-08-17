"""One diagnostic History writer-stage smoke — cached ledger, no extraction/alignment.

Writes evals/history/diagnostic_ladder/run-<stamp>/. Do not sweep.
"""

from __future__ import annotations

import argparse
import hashlib
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
from history_langfuse import flush_langfuse
from history_structure import structure_spec_hash
from history_writer import (
    DIAGNOSTIC_BANNER,
    TABLE_POSITION_MARKER,
    TRACE_ALIGNMENT_STATUS,
    WriterSectionOutput,
    attach_plan_identity,
    plan_writer_calls,
    render_diagnostic_section,
    writer_prompt_hash,
)
from evals.panel_checks import score_history_record
from langfuse import observe
from provider import BASTION_MODEL, DRAFT_TEMPERATURE, ModelProvider, compute_cost_usd
from schemas import Ledger

_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_OUT_ROOT = _WEEK1 / "evals" / "history" / "diagnostic_ladder"
_BRIEFS = _WEEK1 / "evals" / "history" / "briefs"


def _sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_ledger() -> Ledger:
    raw = json.loads(_CACHE.read_text(encoding="utf-8"))
    return Ledger.model_validate(raw["ledger"] if "ledger" in raw else raw)


@observe(name="eval.history.writer_ladder.fixture_001")
def _write_section(provider: ModelProvider, *, model: str, messages: list[dict]) -> object:
    return provider.complete_structured(
        model=model,
        messages=messages,
        schema=WriterSectionOutput,
        temperature=DRAFT_TEMPERATURE,
    )


def _banner_page(body: str) -> str:
    return f"{DIAGNOSTIC_BANNER}\n\n{body.rstrip()}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("openai", "bastion"),
        default="openai",
        help="Writer backend. Uses the 8/14 package: structure, compiler, short prompt, Phase 1 examples, concise brief.",
    )
    args = parser.parse_args(argv)

    if not _CACHE.is_file():
        print(f"Missing cached ledger: {_CACHE}", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = _OUT_ROOT / f"run-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    sections_dir = run_dir / "sections"
    sections_dir.mkdir()

    ledger = _load_ledger()
    conflicts, variance, *_ = detect_disagreements_from_ledger(ledger)
    plan, requests = plan_writer_calls(
        ledger, conflicts=conflicts, variance=variance
    )
    if args.provider == "bastion":
        provider = ModelProvider(backend="bastion")
        model = BASTION_MODEL
        cost_usd: float | None = None
    else:
        provider = ModelProvider()
        model = "gpt-4o-mini"
        cost_usd = 0.0

    call_count = 0
    tokens_used = 0
    prompt_tokens = 0
    completion_tokens = 0
    assembled: list[str] = [DIAGNOSTIC_BANNER, ""]
    section_results: list[dict] = []
    start = time.perf_counter()

    try:
        for req in requests:
            result = _write_section(provider, model=model, messages=req["messages"])
            call_count += 1
            tokens_used += result.total_tokens
            prompt_tokens += result.prompt_tokens
            completion_tokens += result.completion_tokens
            if cost_usd is not None:
                cost_usd += compute_cost_usd(
                    model, result.prompt_tokens, result.completion_tokens
                )
            output = result.data
            assert isinstance(output, WriterSectionOutput)
            section = next(
                s for s in plan.sections if s.section_key == req["section_key"]
            )
            attached = attach_plan_identity(
                output, section, req["offered_evidence_ids"]
            )
            readable = render_diagnostic_section(req["display_label"], attached)
            assembled.append(readable)
            assembled.append("")
            record = {
                "section_key": req["section_key"],
                "display_label": req["display_label"],
                "example_id": req["example_id"],
                "example_text_sha256": req["example_text_sha256"],
                "evidence_brief_sha256": req["evidence_brief_sha256"],
                "writer_prompt_hash": req["writer_prompt_hash"],
                "provider": args.provider,
                "model": model,
                "messages_sha256": req["messages_sha256"],
                "trace_alignment_status": TRACE_ALIGNMENT_STATUS,
                "tokens": {
                    "total": result.total_tokens,
                    "prompt": result.prompt_tokens,
                    "completion": result.completion_tokens,
                },
                "raw_output": output.model_dump(),
                "attached_blocks": attached,
                "offered_evidence_ids": req["offered_evidence_ids"],
            }
            section_results.append(record)
            (sections_dir / f"{req['section_key']}.json").write_text(
                json.dumps(
                    {
                        **record,
                        "messages": req["messages"],
                        "case_payload": req["case_payload"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (sections_dir / f"{req['section_key']}.md").write_text(
                _banner_page(readable), encoding="utf-8"
            )
    finally:
        flush_langfuse()

    latency_ms = int((time.perf_counter() - start) * 1000)
    assembled_text = "\n".join(assembled).rstrip() + "\n"
    (run_dir / "assembled.md").write_text(
        assembled_text, encoding="utf-8"
    )

    brief_hashes = {}
    for name in (
        "current_status_history.json",
        "educational_history.json",
        "previous_evaluations.json",
        "rater_input.json",
    ):
        brief_hashes[name] = _sha_file(_BRIEFS / name)

    manifest = {
        "banner": DIAGNOSTIC_BANNER,
        "fixture_id": "fixture_001",
        "upstream_parent": "unaccepted cached ledger/brief",
        "package": "positive_history_writer",
        "provider": args.provider,
        "model": model,
        "temperature": DRAFT_TEMPERATURE,
        "call_count": call_count,
        "tokens_used": tokens_used,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": None if cost_usd is None else round(cost_usd, 6),
        "latency_ms": latency_ms,
        "writer_prompt_hash": writer_prompt_hash("Current Status & History"),
        "structure_spec_id": "provisional_tj_v1",
        "structure_spec_hash": structure_spec_hash("provisional_tj_v1"),
        "cached_ledger_path": str(_CACHE.relative_to(_WEEK1)),
        "cached_ledger_sha256": _sha_file(_CACHE),
        "compiled_brief_sha256": brief_hashes,
        "example_hashes": [
            {
                "section_key": r["section_key"],
                "example_id": r["example_id"],
                "example_text_sha256": r["example_text_sha256"],
                "evidence_brief_sha256": r["evidence_brief_sha256"],
            }
            for r in section_results
        ],
        "trace_alignment_status": TRACE_ALIGNMENT_STATUS,
        "skip_entailment": True,
        "chart_composer": "not_exercised",
        "table_position_marker": TABLE_POSITION_MARKER,
        "section_keys": [r["section_key"] for r in section_results],
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    ladder = f"""{DIAGNOSTIC_BANNER}

# Diagnostic ladder report — writer stage

**Run:** `{run_dir.name}`
**Package:** positive History writer (`history_writer.py` / `history_writer_prompt.md` / Phase 1 examples / concise brief / `provisional_tj_v1`)
**Provider:** {args.provider} · **Model:** {model} · temperature {DRAFT_TEMPERATURE}
**Writer calls:** {call_count}
**Tokens:** {tokens_used} (prompt {prompt_tokens} / completion {completion_tokens})
**Cost USD:** {("unknown" if cost_usd is None else round(cost_usd, 6))}
**trace_alignment_status:** `{TRACE_ALIGNMENT_STATUS}`

| Stage | What this run can establish | Current status |
|---|---|---|
| source → raw extraction | already reviewed on the seven-item slice | known failures; not rerun |
| raw extraction → deterministic disposition | drops are visible | correct rejection can still lose useful evidence |
| disposition → ledger | exact cached parent identifiable | provisional / not accepted; sha `{manifest['cached_ledger_sha256']}` |
| ledger → brief | section/block routing and omissions inspectable | compiled briefs hashed in manifest; writer received a concise subset |
| brief → prose | intended short prompt + full example can compose a coherent section | {call_count} writer calls; see assembled.md |
| prose → trace alignment | not exercised in this task | `{TRACE_ALIGNMENT_STATUS}` |
| chart composition | not exercised in this task | queued independent lane; table position marked |

## What to evaluate (separate; not one score)

Fill after reading `assembled.md`. Do not retune the prompt from this output.

1. Evidence-supported sections/blocks in server-owned order — see attached_blocks.
2. Full Molly example visible — assistant message is the complete Phase 1 section.
3. Concise brief — case user JSON has evidence items, not fact/timeline/variance dumps.
4. Prose vs failed long-policy smoke — human read.
5. Invented claims — flag for review; do not repair.
6. Inherited ledger/brief defects vs writer-introduced defects — human read.
7. Next rung after Bastion — accepted ledger parent, chart composer, trace alignment.

HARD STOP. No retune. No sweep. No extraction call.
"""
    (run_dir / "ladder_report.md").write_text(ladder, encoding="utf-8")

    print(assembled_text)
    print(f"run_dir={run_dir}")
    print(f"call_count={call_count}")
    print(
        f"tokens={tokens_used} cost_usd={cost_usd} latency_ms={latency_ms} "
        f"provider={args.provider} model={model}"
    )
    print()
    print("TRACE checks vs 20-run baseline (opener 0/20 pass; n=20)")
    score_record = {
        "rendered_prose": assembled_text,
        "sections": [
            {
                "display_label": row["display_label"],
                "prose": "\n\n".join(
                    f"**{b['display_label']}:** {b.get('prose') or ''}"
                    for b in row.get("attached_blocks") or []
                ),
            }
            for row in section_results
        ],
    }
    for check in score_history_record(score_record):
        mark = "pass" if check.passed else "fail"
        print(f"  {check.name}: {mark} — {check.detail}")
    print("HARD STOP — traced writer-stage diagnostic only; no retune / no sweep.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
