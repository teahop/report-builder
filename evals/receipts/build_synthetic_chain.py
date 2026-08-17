"""Fully synthetic extract→transform→ledger→accept→brief chain (no network).

Decisions use ``receipt_test_harness`` / ``synthetic_test`` only — never a human id.
Terminal brief remains unreviewed unless a later decision is recorded.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.receipts.hashing import sha256_canonical, sha256_text  # noqa: E402
from evals.receipts.models import (  # noqa: E402
    SYNTHETIC_REVIEWER_ID,
    SYNTHETIC_REVIEWER_ROLE,
    ArtifactRef,
    BriefDisposition,
    ExtractDisposition,
    QuarantineReviewItem,
    StageConfig,
)
from evals.receipts.review import (  # noqa: E402
    ReviewError,
    record_decision,
    rebuild_review_index,
    require_accepted_parent,
    review_status,
)
from evals.receipts.stage_evals import append_eval_record  # noqa: E402
from evals.receipts.store import ReceiptStore, build_receipt, new_run_id  # noqa: E402
from evals.receipts.validate import (  # noqa: E402
    validate_brief_dispositions,
    validate_extract_dispositions,
)

STRUCTURE_SPEC_ID = "provisional_tj_v1"
STRUCTURE_STUB = {"structure_spec_id": STRUCTURE_SPEC_ID, "blocks": ["health_history"]}


def _harness_accept(store: ReceiptStore, run_id: str, artifact_id: str, notes: str) -> None:
    record_decision(
        store,
        run_id=run_id,
        artifact_id=artifact_id,
        decision="accepted",
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
        notes=notes,
    )


def build_synthetic_chain(store: ReceiptStore | None = None) -> dict:
    store = store or ReceiptStore()
    run_id = new_run_id("synthetic-history-chain")

    chunk_sha = sha256_text("synthetic chunk body about sleep and meds")
    raw_items = [
        {
            "index": 0,
            "predicate": "sleep",
            "value": "poor",
            "value_text": "sleep is poor without medication",
            "reporter": "Parent A",
        },
        {
            "index": 1,
            "predicate": "medications",
            "value": "melatonin",
            "value_text": "takes melatonin at night",
            "reporter": "Parent A",
        },
        {
            "index": 2,
            "predicate": "grade",
            "value": "12",
            "value_text": "future 12th grade semester plan",
            "reporter": None,
        },
        {
            "index": 3,
            "predicate": "medications",
            "value": "melatonin",
            "value_text": "takes melatonin at night",
            "reporter": "Parent A",
        },
    ]
    raw_item_ids = [
        f"syn:chunk:{chunk_sha[:12]}:raw:{i:03d}" for i in range(len(raw_items))
    ]
    raw_machine = {
        "source_id": "syn_doc_01",
        "chunk_sha256": chunk_sha,
        "raw_drafts": raw_items,
        "item_ids": raw_item_ids,
    }
    raw_receipt = build_receipt(
        store=store,
        run_id=run_id,
        stage="extract_raw",
        machine_payload=raw_machine,
        config=StageConfig(
            model="fake-extract-0",
            temperature=0.0,
            prompt_sha256=sha256_text("synthetic extract prompt"),
            code_fingerprint="synthetic-chain-v2",
        ),
        counts={"raw_items": len(raw_items)},
        tokens={"total_tokens": 42},
        lineage="evaluable",
        notes="Synthetic raw extraction — fake provider, no network.",
        artifact_id="art_syn_extract_raw_v2",
    )
    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=raw_receipt.artifact_id,
        check_id="expected_claim_presence",
        check_version="1",
        result="pass",
        evidence_item_ids=raw_item_ids[:2],
        detail="sleep + medications claims present",
        evaluator_id=SYNTHETIC_REVIEWER_ID,
        evaluator_origin="synthetic_test",
    )

    dispositions = [
        ExtractDisposition(
            item_id=raw_item_ids[0], kind="retained", fact_id="f_syn_001"
        ),
        ExtractDisposition(
            item_id=raw_item_ids[1],
            kind="transformed",
            fact_id="f_syn_002",
            before={"value": "melatonin"},
            after={"value": "melatonin 2.5mg"},
            reason="normalize_medications",
            gate_or_check="normalize",
        ),
        ExtractDisposition(
            item_id=raw_item_ids[2],
            kind="quarantined",
            review_item_id="q_syn_grade_future",
            reason="spurious_future_grade",
            gate_or_check="future_grade_heuristic",
        ),
        ExtractDisposition(
            item_id=raw_item_ids[3],
            kind="suppressed_duplicate",
            canonical_fact_id="f_syn_002",
        ),
    ]
    counts = validate_extract_dispositions(
        raw_item_ids, dispositions, lineage="evaluable"
    )
    quarantine = [
        QuarantineReviewItem(
            review_item_id="q_syn_grade_future",
            item_id=raw_item_ids[2],
            reason="spurious_future_grade",
            detail={"value_text": raw_items[2]["value_text"]},
        )
    ]
    transform_decisions = {
        "dispositions": [d.model_dump(mode="json") for d in dispositions],
        "quarantine_review_items": [q.model_dump(mode="json") for q in quarantine],
    }
    transform_machine = {
        "facts": [
            {
                "id": "f_syn_001",
                "predicate": "sleep",
                "value": "poor",
                "value_text": raw_items[0]["value_text"],
                "reporter": "Parent A",
            },
            {
                "id": "f_syn_002",
                "predicate": "medications",
                "value": "melatonin 2.5mg",
                "value_text": raw_items[1]["value_text"],
                "reporter": "Parent A",
            },
        ],
        "parent_raw_artifact_id": raw_receipt.artifact_id,
        "parent_raw_sha256": raw_receipt.artifact_sha256,
    }

    _harness_accept(
        store,
        run_id,
        raw_receipt.artifact_id,
        "synthetic_test acceptance for parent-gate mechanics only",
    )
    require_accepted_parent(
        store,
        run_id=run_id,
        artifact_id=raw_receipt.artifact_id,
        expected_sha256=raw_receipt.artifact_sha256,
    )

    transform_receipt = build_receipt(
        store=store,
        run_id=run_id,
        stage="extract_transform",
        machine_payload=transform_machine,
        deterministic_decisions=transform_decisions,
        config=StageConfig(code_fingerprint="synthetic-chain-v2"),
        parents=[
            ArtifactRef(
                stage="extract_raw",
                artifact_id=raw_receipt.artifact_id,
                sha256=raw_receipt.artifact_sha256,
                required_accepted=True,
            )
        ],
        counts=counts,
        lineage="evaluable",
        artifact_id="art_syn_extract_transform_v2",
    )
    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=transform_receipt.artifact_id,
        check_id="transform_total_accounting",
        check_version="1",
        result="pass",
        detail=str(counts),
        evaluator_id=SYNTHETIC_REVIEWER_ID,
        evaluator_origin="synthetic_test",
    )

    _harness_accept(
        store,
        run_id,
        transform_receipt.artifact_id,
        "synthetic_test acceptance for parent-gate mechanics only",
    )
    ledger_machine = {
        "child": {"name": "Syn Child", "dob": "2015-01-01", "evaluation_date": "2025-06-01"},
        "facts": transform_machine["facts"],
        "sources": [{"id": "syn_doc_01", "label": "Synthetic parent interview"}],
        "parent_transform_sha256": transform_receipt.artifact_sha256,
    }
    ledger_receipt = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload=ledger_machine,
        config=StageConfig(schema_version="1", code_fingerprint="synthetic-chain-v2"),
        parents=[
            ArtifactRef(
                stage="extract_transform",
                artifact_id=transform_receipt.artifact_id,
                sha256=transform_receipt.artifact_sha256,
                required_accepted=True,
            )
        ],
        counts={"facts": 2},
        lineage="evaluable",
        artifact_id="art_syn_ledger_v2",
    )
    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=ledger_receipt.artifact_id,
        check_id="ledger_known_facts",
        check_version="1",
        result="pass",
        evidence_item_ids=["f_syn_001", "f_syn_002"],
        evaluator_id=SYNTHETIC_REVIEWER_ID,
        evaluator_origin="synthetic_test",
    )

    preview_attempted = False
    try:
        require_accepted_parent(
            store,
            run_id=run_id,
            artifact_id=ledger_receipt.artifact_id,
            expected_sha256=ledger_receipt.artifact_sha256,
        )
    except ReviewError:
        preview_attempted = True
        build_receipt(
            store=store,
            run_id=run_id,
            stage="brief",
            machine_payload={"preview": True, "sections": []},
            parents=[
                ArtifactRef(
                    stage="ledger",
                    artifact_id=ledger_receipt.artifact_id,
                    sha256=ledger_receipt.artifact_sha256,
                    required_accepted=False,
                )
            ],
            lineage="non_evaluable_preview",
            notes=(
                "NON-EVALUABLE PREVIEW — ledger not yet accepted. "
                "Must not masquerade as an accepted brief."
            ),
            artifact_id="art_syn_brief_preview_unreviewed_v2",
        )

    _harness_accept(
        store,
        run_id,
        ledger_receipt.artifact_id,
        "synthetic_test acceptance for parent-gate mechanics only",
    )

    fact_ids = ["f_syn_001", "f_syn_002"]
    brief_disps = [
        BriefDisposition(
            fact_id="f_syn_001",
            kind="selected",
            destinations=["current_status_history/health_history"],
        ),
        BriefDisposition(
            fact_id="f_syn_002",
            kind="selected",
            destinations=[
                "current_status_history/health_history",
                "rater_input/caregiver_input:parent_a",
            ],
        ),
    ]
    brief_counts = validate_brief_dispositions(fact_ids, brief_disps)
    brief_decisions = {
        "brief_dispositions": [d.model_dump(mode="json") for d in brief_disps],
    }
    structure_sha = sha256_canonical(STRUCTURE_STUB)
    brief_machine = {
        "structure_spec_id": STRUCTURE_SPEC_ID,
        "structure_spec_sha256": structure_sha,
        "sections": [
            {
                "section_key": "current_status_history",
                "blocks": [
                    {
                        "block_key": "health_history",
                        "fact_ids": ["f_syn_001", "f_syn_002"],
                    }
                ],
            }
        ],
        "parent_ledger_sha256": ledger_receipt.artifact_sha256,
    }
    brief_receipt = build_receipt(
        store=store,
        run_id=run_id,
        stage="brief",
        machine_payload=brief_machine,
        deterministic_decisions=brief_decisions,
        config=StageConfig(
            structure_spec_id=STRUCTURE_SPEC_ID,
            structure_spec_sha256=structure_sha,
            code_fingerprint="synthetic-chain-v2",
        ),
        parents=[
            ArtifactRef(
                stage="ledger",
                artifact_id=ledger_receipt.artifact_id,
                sha256=ledger_receipt.artifact_sha256,
                required_accepted=True,
            )
        ],
        counts=brief_counts,
        lineage="evaluable",
        artifact_id="art_syn_brief_v2",
    )
    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=brief_receipt.artifact_id,
        check_id="brief_routing_accounting",
        check_version="1",
        result="pass",
        detail=str(brief_counts),
        evaluator_id=SYNTHETIC_REVIEWER_ID,
        evaluator_origin="synthetic_test",
    )
    # Intentionally do NOT auto-accept the terminal brief.
    assert review_status(store, run_id, brief_receipt.artifact_id) == "unreviewed"

    rebuild_review_index(store, run_id)

    # Guard: no human ids in decisions for this run.
    decisions_file = store.run_dir(run_id) / "decisions.jsonl"
    decision_text = decisions_file.read_text(encoding="utf-8").lower()
    for banned in ("\"tj\"", "\"molly\"", "teahop"):
        assert banned not in decision_text, f"banned identity found: {banned}"

    manifest = {
        "run_id": run_id,
        "preview_blocked_until_accept": preview_attempted,
        "artifacts": {
            "extract_raw": {
                "artifact_id": raw_receipt.artifact_id,
                "sha256": raw_receipt.artifact_sha256,
                "evidence_view_sha256": raw_receipt.evidence_view.sha256
                if raw_receipt.evidence_view
                else None,
            },
            "extract_transform": {
                "artifact_id": transform_receipt.artifact_id,
                "sha256": transform_receipt.artifact_sha256,
            },
            "ledger": {
                "artifact_id": ledger_receipt.artifact_id,
                "sha256": ledger_receipt.artifact_sha256,
            },
            "brief_preview_non_evaluable": {
                "artifact_id": "art_syn_brief_preview_unreviewed_v2",
            },
            "brief": {
                "artifact_id": brief_receipt.artifact_id,
                "sha256": brief_receipt.artifact_sha256,
                "review_status": "unreviewed",
            },
        },
        "chain": [
            raw_receipt.artifact_sha256,
            transform_receipt.artifact_sha256,
            ledger_receipt.artifact_sha256,
            brief_receipt.artifact_sha256,
        ],
        "decision_origin": "synthetic_test",
        "reviewer_id": SYNTHETIC_REVIEWER_ID,
    }
    out = store.run_dir(run_id) / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    print(json.dumps(build_synthetic_chain(), indent=2))


if __name__ == "__main__":
    main()
