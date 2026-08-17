"""Full diagnostic History ladder: extract → ledger → brief → writer.

Does not overwrite evals/cache/fixture_001_ledger.json or evals/history/briefs/.
Does not auto-accept the ledger. Chart composer and trace alignment stay later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from dotenv import load_dotenv

load_dotenv(_WEEK1 / ".env")

from conflicts import detect_disagreements_from_ledger
from evals.panel_checks import score_history_record
from evals.receipts.hashing import sha256_text
from evals.receipts.models import ArtifactRef, StageConfig
from evals.receipts.store import ReceiptStore, build_receipt, new_run_id
from extract import (
    EXTRACT_SYSTEM_PROMPT,
    build_ledger,
)
from history_compiler import (
    case_brief_json,
    compile_history_plan,
    render_evidence_brief_markdown,
)
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
from langfuse import observe
from provider import (
    BASTION_MODEL,
    DRAFT_TEMPERATURE,
    EXTRACT_TEMPERATURE,
    ModelProvider,
    compute_cost_usd,
)
from test_all_stages import FIXTURE_001_MANIFEST_PATH, load_case_manifest

_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_OUT_ROOT = _WEEK1 / "evals" / "history" / "diagnostic_ladder"


class RecordingProvider:
    """Wraps ModelProvider and keeps every structured call's raw text."""

    def __init__(self, inner: ModelProvider) -> None:
        self._inner = inner
        self.calls: list[dict[str, Any]] = []

    def complete_structured(self, *args: Any, **kwargs: Any) -> Any:
        result = self._inner.complete_structured(*args, **kwargs)
        user = kwargs.get("user") or ""
        source_id = None
        try:
            source_id = json.loads(user)["source"]["id"]
        except (TypeError, ValueError, KeyError):
            pass
        parsed = None
        data = getattr(result, "data", None)
        if data is not None and hasattr(data, "model_dump"):
            parsed = data.model_dump(mode="json")
        self.calls.append(
            {
                "source_id": source_id,
                "schema": getattr(kwargs.get("schema"), "__name__", None),
                "temperature": kwargs.get("temperature"),
                "user_sha256": sha256_text(user) if isinstance(user, str) else None,
                "raw_text": getattr(result, "raw_text", None),
                "parsed": parsed,
                "tokens": {
                    "total": getattr(result, "total_tokens", 0),
                    "prompt": getattr(result, "prompt_tokens", 0),
                    "completion": getattr(result, "completion_tokens", 0),
                },
            }
        )
        return result


def _sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _banner_page(body: str) -> str:
    return f"{DIAGNOSTIC_BANNER}\n\n{body.rstrip()}\n"


@observe(name="eval.history.full_ladder.extract_source")
def _extract_source(provider: RecordingProvider, **kwargs: Any) -> Any:
    return build_ledger(provider, **kwargs)  # type: ignore[arg-type]


@observe(name="eval.history.full_ladder.write_section")
def _write_section(provider: ModelProvider, *, model: str, messages: list[dict]) -> object:
    return provider.complete_structured(
        model=model,
        messages=messages,
        schema=WriterSectionOutput,
        temperature=DRAFT_TEMPERATURE,
    )


def _compile_briefs(ledger: Any, out_dir: Path) -> dict[str, str | None]:
    conflicts, variance, *_ = detect_disagreements_from_ledger(ledger)
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    out_dir.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str | None] = {}
    for section in plan.sections:
        md = render_evidence_brief_markdown(
            plan, section, ledger, conflicts=conflicts, variance=variance
        )
        md_path = out_dir / f"{section.section_key}.md"
        md_path.write_text(_banner_page(md), encoding="utf-8")
        brief = case_brief_json(
            plan,
            section,
            ledger,
            conflicts=conflicts,
            variance=variance,
            reuse_records=[],
            fewshots=[],
        )
        json_path = out_dir / f"{section.section_key}.json"
        json_path.write_text(brief + "\n", encoding="utf-8")
        hashes[json_path.name] = _sha_file(json_path)
    return hashes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("openai", "bastion"),
        default="bastion",
        help="Extract and write on the same backend. Default: bastion.",
    )
    args = parser.parse_args(argv)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = _OUT_ROOT / f"run-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = run_dir / "extract"
    extract_dir.mkdir()
    sections_dir = run_dir / "sections"
    sections_dir.mkdir()
    briefs_dir = run_dir / "briefs"
    receipt_run_id = new_run_id("bastion-full-ladder")

    if args.provider == "bastion":
        inner = ModelProvider(backend="bastion")
        model = BASTION_MODEL
        cost_usd: float | None = None
    else:
        inner = ModelProvider()
        model = "gpt-4o-mini"
        cost_usd = 0.0
    provider = RecordingProvider(inner)

    child, sources, _keys = load_case_manifest(FIXTURE_001_MANIFEST_PATH)
    ledger = None
    extract_tokens = 0
    extract_prompt = 0
    extract_completion = 0
    extract_call_count = 0
    tokens_by_source: dict[str, int] = {}
    extract_failures: list[dict[str, str]] = []
    predicates_for_review: list[str] = []
    subjects_for_review: list[str] = []
    start = time.perf_counter()

    print(f"FULL LADDER extract→ledger→brief→writer  provider={args.provider} model={model}")
    print(f"run_dir={run_dir}")
    print("Does not overwrite evals/cache/fixture_001_ledger.json")
    print()

    try:
        for source in sources:
            before = len(provider.calls)
            label = "SKIP-score" if source.doc_class == "score_report" else "EXTRACT"
            print(f"  {label} {source.id} {source.label!r} …", flush=True)
            t0 = time.perf_counter()
            try:
                ledger, toks, p_tok, c_tok, review, subj_review, *_rest = _extract_source(
                    provider,
                    child=child,
                    sources=[source],
                    model=model,
                    prior_ledger=ledger,
                )
            except Exception as exc:  # noqa: BLE001 — record then abort
                raw = getattr(exc, "raw_text", None)
                extract_failures.append(
                    {
                        "source_id": source.id,
                        "error": f"{type(exc).__name__}: {exc}",
                        "raw_text_chars": len(raw or ""),
                    }
                )
                (extract_dir / "failures.json").write_text(
                    json.dumps(extract_failures, indent=2) + "\n", encoding="utf-8"
                )
                if raw:
                    (extract_dir / f"{source.id}_parse_error.txt").write_text(
                        raw, encoding="utf-8"
                    )
                print(f"    FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
                return 1
            tokens_by_source.update(toks)
            extract_tokens += sum(toks.values())
            extract_prompt += p_tok
            extract_completion += c_tok
            for name in review:
                if name not in predicates_for_review:
                    predicates_for_review.append(name)
            for name in subj_review:
                if name not in subjects_for_review:
                    subjects_for_review.append(name)
            new_calls = provider.calls[before:]
            extract_call_count += len(new_calls)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            extra = f" new_predicates={review}" if review else ""
            print(
                f"    chunks={len(new_calls)} facts_so_far={len(ledger.facts)} "
                f"ms={elapsed_ms}{extra}",
                flush=True,
            )
            for i, call in enumerate(new_calls):
                chunk_path = extract_dir / f"{source.id}_chunk{i:02d}.json"
                chunk_path.write_text(
                    json.dumps(call, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                raw = call.get("raw_text") or ""
                (extract_dir / f"{source.id}_chunk{i:02d}.txt").write_text(
                    raw, encoding="utf-8"
                )
            (run_dir / "ledger_partial.json").write_text(
                json.dumps(
                    {
                        "banner": DIAGNOSTIC_BANNER,
                        "last_source_id": source.id,
                        "facts": len(ledger.facts),
                        "ledger": ledger.model_dump(mode="json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    finally:
        flush_langfuse()

    assert ledger is not None
    extract_ms = int((time.perf_counter() - start) * 1000)
    ledger_path = run_dir / "ledger.json"
    ledger_payload = {
        "banner": DIAGNOSTIC_BANNER,
        "provider": args.provider,
        "model": model,
        "extract_temperature": EXTRACT_TEMPERATURE,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "extract_call_count": extract_call_count,
        "tokens_by_source": tokens_by_source,
        "ledger": ledger.model_dump(mode="json"),
    }
    ledger_path.write_text(
        json.dumps(ledger_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"extract done calls={extract_call_count} facts={len(ledger.facts)} "
        f"ms={extract_ms} predicates_for_review={predicates_for_review}"
    )

    brief_hashes = _compile_briefs(ledger, briefs_dir)
    print(f"briefs compiled under {briefs_dir.relative_to(_WEEK1)}")

    store = ReceiptStore()
    extract_receipt = build_receipt(
        store=store,
        run_id=receipt_run_id,
        stage="extract_raw",
        machine_payload={
            "provider": args.provider,
            "model": model,
            "extract_temperature": EXTRACT_TEMPERATURE,
            "system_prompt_sha256": sha256_text(EXTRACT_SYSTEM_PROMPT),
            "calls": provider.calls,
        },
        config=StageConfig(
            model=model,
            temperature=EXTRACT_TEMPERATURE,
            prompt_sha256=sha256_text(EXTRACT_SYSTEM_PROMPT),
            extra={"provider": args.provider, "fixture_id": "fixture_001"},
        ),
        counts={
            "extract_calls": extract_call_count,
            "sources": len(sources),
        },
        tokens={
            "total": extract_tokens,
            "prompt": extract_prompt,
            "completion": extract_completion,
        },
        latency_ms=extract_ms,
        lineage="evaluable",
        notes="Diagnostic complete-case extract. Not human-accepted.",
    )
    ledger_receipt = build_receipt(
        store=store,
        run_id=receipt_run_id,
        stage="ledger",
        machine_payload=ledger_payload,
        config=StageConfig(
            model=model,
            schema_version="1",
            extra={"provider": args.provider},
        ),
        parents=[
            ArtifactRef(
                stage="extract_raw",
                artifact_id=extract_receipt.artifact_id,
                sha256=extract_receipt.artifact_sha256,
                required_accepted=False,
            )
        ],
        counts={"facts": len(ledger.facts), "sources": len(ledger.sources)},
        lineage="evaluable",
        notes="Unaccepted diagnostic parent. Do not overwrite fixture_001 cache.",
    )
    brief_receipt = build_receipt(
        store=store,
        run_id=receipt_run_id,
        stage="brief",
        machine_payload={
            "structure_spec_id": "provisional_tj_v1",
            "compiled_brief_sha256": brief_hashes,
        },
        config=StageConfig(structure_spec_id="provisional_tj_v1"),
        parents=[
            ArtifactRef(
                stage="ledger",
                artifact_id=ledger_receipt.artifact_id,
                sha256=ledger_receipt.artifact_sha256,
                required_accepted=False,
            )
        ],
        lineage="evaluable",
        notes="Compiled from this run's Bastion ledger, not the cached OpenAI parent.",
    )

    conflicts, variance, *_ = detect_disagreements_from_ledger(ledger)
    plan, requests = plan_writer_calls(
        ledger, conflicts=conflicts, variance=variance
    )
    writer_provider = inner
    call_count = 0
    tokens_used = 0
    prompt_tokens = 0
    completion_tokens = 0
    assembled: list[str] = [DIAGNOSTIC_BANNER, ""]
    section_results: list[dict] = []
    write_start = time.perf_counter()

    try:
        for req in requests:
            print(f"  WRITE {req['section_key']} …", flush=True)
            result = _write_section(
                writer_provider, model=model, messages=req["messages"]
            )
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

    write_ms = int((time.perf_counter() - write_start) * 1000)
    assembled_text = "\n".join(assembled).rstrip() + "\n"
    (run_dir / "assembled.md").write_text(assembled_text, encoding="utf-8")

    draft_receipt = build_receipt(
        store=store,
        run_id=receipt_run_id,
        stage="draft",
        machine_payload={
            "assembled": assembled_text,
            "section_keys": [r["section_key"] for r in section_results],
        },
        config=StageConfig(
            model=model,
            temperature=DRAFT_TEMPERATURE,
            prompt_sha256=writer_prompt_hash("Current Status & History"),
            structure_spec_id="provisional_tj_v1",
        ),
        parents=[
            ArtifactRef(
                stage="brief",
                artifact_id=brief_receipt.artifact_id,
                sha256=brief_receipt.artifact_sha256,
                required_accepted=False,
            )
        ],
        counts={"writer_calls": call_count},
        tokens={
            "total": tokens_used,
            "prompt": prompt_tokens,
            "completion": completion_tokens,
        },
        latency_ms=write_ms,
        lineage="evaluable",
        notes="Positive History writer. Trace alignment not run. Ledger not accepted.",
    )

    cached_sha = _sha_file(_CACHE)
    ledger_sha = _sha_file(ledger_path)
    manifest = {
        "banner": DIAGNOSTIC_BANNER,
        "fixture_id": "fixture_001",
        "package": "positive_history_full_ladder",
        "upstream_parent": "this run's unaccepted Bastion extract/ledger",
        "provider": args.provider,
        "model": model,
        "extract_temperature": EXTRACT_TEMPERATURE,
        "draft_temperature": DRAFT_TEMPERATURE,
        "extract_call_count": extract_call_count,
        "writer_call_count": call_count,
        "extract_tokens": {
            "total": extract_tokens,
            "prompt": extract_prompt,
            "completion": extract_completion,
        },
        "writer_tokens": {
            "total": tokens_used,
            "prompt": prompt_tokens,
            "completion": completion_tokens,
        },
        "cost_usd": None if cost_usd is None else round(cost_usd, 6),
        "extract_latency_ms": extract_ms,
        "writer_latency_ms": write_ms,
        "facts": len(ledger.facts),
        "predicates_for_review": predicates_for_review,
        "subjects_for_review": subjects_for_review,
        "writer_prompt_hash": writer_prompt_hash("Current Status & History"),
        "extract_prompt_sha256": sha256_text(EXTRACT_SYSTEM_PROMPT),
        "structure_spec_id": "provisional_tj_v1",
        "structure_spec_hash": structure_spec_hash("provisional_tj_v1"),
        "did_not_overwrite_cache": True,
        "cached_openai_ledger_sha256": cached_sha,
        "this_run_ledger_path": str(ledger_path.relative_to(_WEEK1)),
        "this_run_ledger_sha256": ledger_sha,
        "compiled_brief_sha256": brief_hashes,
        "receipt_run_id": receipt_run_id,
        "receipts": {
            "extract_raw": extract_receipt.artifact_id,
            "ledger": ledger_receipt.artifact_id,
            "brief": brief_receipt.artifact_id,
            "draft": draft_receipt.artifact_id,
        },
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
        "tokens_by_source": tokens_by_source,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    ladder = f"""{DIAGNOSTIC_BANNER}

# Diagnostic ladder report — extract → ledger → brief → writer

**Run:** `{run_dir.name}`
**Package:** positive History writer on a same-provider extract
**Provider:** {args.provider} · **Model:** {model}
**Extract calls:** {extract_call_count} (temp {EXTRACT_TEMPERATURE})
**Writer calls:** {call_count} (temp {DRAFT_TEMPERATURE})
**Facts in this ledger:** {len(ledger.facts)}
**Did not overwrite** `evals/cache/fixture_001_ledger.json` (sha `{cached_sha}`)
**This-run ledger sha:** `{ledger_sha}`
**Receipts:** `{receipt_run_id}`
**trace_alignment_status:** `{TRACE_ALIGNMENT_STATUS}`

| Stage | What this run can establish | Current status |
|---|---|---|
| source → raw extraction | complete-case Bastion extract; raw text retained per chunk | {extract_call_count} calls; unaccepted |
| raw extraction → deterministic disposition | production extract gates applied | inspect extract/ and ledger.json |
| disposition → ledger | exact parent identifiable | provisional / not accepted; sha `{ledger_sha}` |
| ledger → brief | compiled from this ledger, not the OpenAI cache | hashed in manifest |
| brief → prose | short prompt + Phase 1 examples | {call_count} writer calls; see assembled.md |
| prose → trace alignment | not exercised | `{TRACE_ALIGNMENT_STATUS}` |
| chart composition | not exercised | table position marked |

HARD STOP. No retune. No sweep. Ledger not accepted.
"""
    (run_dir / "ladder_report.md").write_text(ladder, encoding="utf-8")

    print()
    print(assembled_text)
    print(f"run_dir={run_dir}")
    print(
        f"extract_calls={extract_call_count} writer_calls={call_count} "
        f"facts={len(ledger.facts)} provider={args.provider} model={model}"
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
    print("HARD STOP — full ladder diagnostic; no retune / no sweep / ledger not accepted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
