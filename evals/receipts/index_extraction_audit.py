"""Index the existing History extraction audit as a diagnostic_replay receipt run.

Represents historical ``_draft_is_skippable`` omissions as ``observed_silent_drop``
(not quarantine). Does **not** link to ``evals/cache/fixture_001_ledger.json``.
Makes zero model calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.receipts.hashing import sha256_text  # noqa: E402
from evals.receipts.models import (  # noqa: E402
    ArtifactRef,
    ExtractDisposition,
    StageConfig,
)
from evals.receipts.stage_evals import append_eval_record  # noqa: E402
from evals.receipts.store import ReceiptStore, build_receipt, new_run_id  # noqa: E402
from evals.receipts.validate import (  # noqa: E402
    dispositions_block_evaluable_acceptance,
    validate_extract_dispositions,
)
from evals.receipts.review import rebuild_review_index  # noqa: E402

_AUDIT = _WEEK1 / "evals" / "history" / "extraction_audit"
_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"


def _item_id(source_id: str, chunk_sha: str, raw_index: int, draft: dict) -> str:
    pred = draft.get("predicate")
    if hasattr(pred, "value"):
        pred = pred.value
    stub = sha256_text(
        json.dumps(
            {
                "predicate": pred,
                "value": draft.get("value"),
                "value_text": draft.get("value_text"),
            },
            sort_keys=True,
        )
    )[:12]
    return f"{source_id}:chunk:{chunk_sha[:12]}:raw:{raw_index:03d}:{stub}"


def index_audit(store: ReceiptStore | None = None) -> dict:
    store = store or ReceiptStore()
    summary = json.loads((_AUDIT / "audit_summary.json").read_text(encoding="utf-8"))
    run_id = new_run_id("extract-audit-replay")

    legacy_payload = {
        "path": "evals/cache/fixture_001_ledger.json",
        "lineage": "legacy_untraceable",
        "reason": (
            "Built from the 2026-08-10 live full-fixture extract whose raw "
            "SourceExtraction responses were not retained. The targeted chunk "
            "replay must not be treated as its parent."
        ),
        "cache_model": summary["run"].get("fixture_cache_model"),
        "cache_built_at": summary["run"].get("fixture_cache_built_at"),
        "file_sha256": sha256_text(_CACHE.read_text(encoding="utf-8"))
        if _CACHE.exists()
        else None,
    }
    legacy = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload=legacy_payload,
        config=StageConfig(extra={"legacy": True}),
        lineage="legacy_untraceable",
        notes="Outside the evaluable chain. Do not use as an accepted parent.",
        counts={"facts_unknown": 77},
        artifact_id="art_legacy_fixture_001_ledger",
    )

    chunk_files = sorted(_AUDIT.glob("doc_*_chunk*.json"))
    all_item_ids: list[str] = []
    all_dispositions: list[ExtractDisposition] = []
    chunk_summaries: list[dict] = []
    total_tokens = 0
    silent_drop_count = 0

    for path in chunk_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        chunk_sha = data["chunk_sha256"]
        source_id = data["source_id"]
        total_tokens += int(data.get("total_tokens") or 0)
        raw_drafts = data.get("raw_drafts_before_gates") or []
        retained = {
            (f.get("value_text") or f.get("value") or ""): f.get("id")
            for f in data.get("retained_after_postprocess") or []
        }
        for idx, draft in enumerate(raw_drafts):
            item_id = _item_id(source_id, chunk_sha, idx, draft)
            all_item_ids.append(item_id)
            trace = None
            for t in data.get("draft_trace") or []:
                if t.get("raw_draft") == draft:
                    trace = t
                    break
            if trace is None and idx < len(data.get("draft_trace") or []):
                trace = data["draft_trace"][idx]

            skipped = bool(trace and trace.get("skipped"))
            skip_reason = (trace or {}).get("skip_reason")
            fact_id = (trace or {}).get("retained_fact_id")
            vt = draft.get("value_text") or draft.get("value") or ""

            if skipped:
                # Historical truth: production silently omitted via gate — not quarantine.
                silent_drop_count += 1
                all_dispositions.append(
                    ExtractDisposition(
                        item_id=item_id,
                        kind="observed_silent_drop",
                        gate_or_check="_draft_is_skippable",
                        reason=skip_reason or "extract_gate_skippable",
                    )
                )
            else:
                fid = fact_id or retained.get(vt)
                if fid is None:
                    silent_drop_count += 1
                    all_dispositions.append(
                        ExtractDisposition(
                            item_id=item_id,
                            kind="observed_silent_drop",
                            gate_or_check="postprocess_omission_without_skip_flag",
                            reason="retained_raw_missing_after_postprocess",
                        )
                    )
                else:
                    norm = (trace or {}).get("normalized_value")
                    if norm is not None and str(norm) != str(draft.get("value")):
                        all_dispositions.append(
                            ExtractDisposition(
                                item_id=item_id,
                                kind="transformed",
                                fact_id=fid,
                                before={"value": draft.get("value")},
                                after={"value": norm},
                                reason="normalize_value",
                                gate_or_check="normalize",
                            )
                        )
                    else:
                        all_dispositions.append(
                            ExtractDisposition(
                                item_id=item_id,
                                kind="retained",
                                fact_id=fid,
                            )
                        )

        chunk_summaries.append(
            {
                "file": path.name,
                "source_id": source_id,
                "chunk_index": data.get("chunk_index"),
                "chunk_sha256": chunk_sha,
                "user_payload_sha256": data.get("user_payload_sha256"),
                "system_prompt_sha256": data.get("system_prompt_sha256"),
                "model": data.get("model"),
                "raw_draft_count": len(raw_drafts),
                "total_tokens": data.get("total_tokens"),
            }
        )

    counts = validate_extract_dispositions(
        all_item_ids, all_dispositions, lineage="diagnostic_replay"
    )
    assert counts.get("observed_silent_drop", 0) == silent_drop_count
    assert silent_drop_count == 6, (
        f"expected six observed silent drops from audit, got {silent_drop_count}"
    )
    # No fabricated quarantine ids.
    assert all(d.review_item_id is None for d in all_dispositions)

    machine = {
        "origin": summary["run"].get("origin"),
        "note": summary["run"].get("note"),
        "system_prompt_sha256": summary["run"].get("system_prompt_sha256"),
        "model": summary["run"].get("model"),
        "temperature": summary["run"].get("extract_temperature"),
        "chunks": chunk_summaries,
        "claims": [
            {
                "claim_id": c["claim_id"],
                "role": c["role"],
                "final_fact_id": c.get("final_fact_id"),
                "raw_match_count": len(c.get("raw_matches") or []),
                "defect_owner_doc": "see extraction_audit/README.md",
            }
            for c in summary.get("claims") or []
        ],
        "legacy_ledger_artifact_id": legacy.artifact_id,
        "legacy_ledger_not_parent": True,
        "observed_silent_drop_count": silent_drop_count,
        "blocks_evaluable_acceptance": dispositions_block_evaluable_acceptance(
            all_dispositions
        ),
    }
    decisions = {
        "dispositions": [d.model_dump(mode="json") for d in all_dispositions],
        "quarantine_review_items": [],  # historical run did not mint quarantine items
        "item_ids": all_item_ids,
    }

    raw_receipt = build_receipt(
        store=store,
        run_id=run_id,
        stage="diagnostic_replay",
        machine_payload=machine,
        deterministic_decisions=decisions,
        config=StageConfig(
            prompt_sha256=summary["run"].get("system_prompt_sha256"),
            model=summary["run"].get("model"),
            temperature=summary["run"].get("extract_temperature"),
            extra={
                "origin": summary["run"].get("origin"),
                "audit_dir": "evals/history/extraction_audit",
            },
        ),
        parents=[],
        inputs=[
            ArtifactRef(
                name="extraction_audit_summary",
                sha256=sha256_text(
                    (_AUDIT / "audit_summary.json").read_text(encoding="utf-8")
                ),
                role="diagnostic_source",
                required_accepted=False,
            )
        ],
        counts={**counts, "raw_items": len(all_item_ids), "chunks": len(chunk_files)},
        tokens={"total_tokens": total_tokens},
        lineage="diagnostic_replay",
        notes=(
            "Targeted chunk replay indexed as diagnostic_replay. "
            "Gate skips recorded as observed_silent_drop (historical truth). "
            "Not the parent of art_legacy_fixture_001_ledger / fixture_001_ledger.json. "
            "Cannot become an accepted evaluable parent until a new run accounts "
            "for every item with a valid evaluable disposition."
        ),
        artifact_id="art_extract_audit_replay_v2",
    )

    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=raw_receipt.artifact_id,
        check_id="extract_total_accounting",
        check_version="1",
        result="pass",
        detail=f"accounted {len(all_item_ids)} raw items; "
        f"{silent_drop_count} observed_silent_drop",
        evaluator_id="receipt_indexer",
        evaluator_origin="system",
    )
    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=raw_receipt.artifact_id,
        check_id="not_parent_of_legacy_cache",
        check_version="1",
        result="pass",
        detail=(
            f"legacy marker {legacy.artifact_id} recorded separately; "
            "not listed as parent of diagnostic replay"
        ),
        evaluator_id="receipt_indexer",
        evaluator_origin="system",
    )
    rebuild_review_index(store, run_id)

    manifest = {
        "run_id": run_id,
        "diagnostic_replay_artifact_id": raw_receipt.artifact_id,
        "diagnostic_replay_sha256": raw_receipt.artifact_sha256,
        "evidence_view_sha256": raw_receipt.evidence_view.sha256
        if raw_receipt.evidence_view
        else None,
        "legacy_ledger_artifact_id": legacy.artifact_id,
        "legacy_ledger_sha256": legacy.artifact_sha256,
        "linked_as_parent": False,
        "observed_silent_drop_count": silent_drop_count,
    }
    out = store.run_dir(run_id) / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    print(json.dumps(index_audit(), indent=2))


if __name__ == "__main__":
    main()
