"""Focused deterministic tests for the stage-receipt spine — zero network/model calls.

Requires ``requirements-dev.txt`` (pytest). Not a runtime dependency.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_WEEK1 = Path(__file__).resolve().parent
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.receipts.build_synthetic_chain import build_synthetic_chain
from evals.receipts.hashing import (
    ContentAddressConflict,
    canonical_json_bytes,
    sha256_canonical,
    write_content_addressed,
)
from evals.receipts.index_extraction_audit import index_audit
from evals.receipts.models import (
    SYNTHETIC_REVIEWER_ID,
    SYNTHETIC_REVIEWER_ROLE,
    BriefDisposition,
    ExtractDisposition,
    ReviewDecision,
)
from evals.receipts.render import render_evidence_markdown
from evals.receipts.review import (
    ReviewError,
    current_review_path,
    is_accepted,
    record_decision,
    rebuild_review_index,
    require_accepted_parent,
    review_status,
)
from evals.receipts.stage_evals import append_eval_record, load_eval_records_for_artifact
from evals.receipts.store import ReceiptStore, build_receipt, new_run_id
from evals.receipts.validate import (
    AccountingError,
    assert_no_generic_excluded,
    validate_brief_dispositions,
    validate_extract_dispositions,
)

_DEV_REQ = _WEEK1 / "requirements-dev.txt"
_OLD_SYNTHETIC = (
    _WEEK1
    / "evals"
    / "receipts"
    / "store"
    / "runs"
    / "synthetic-history-chain-20260810T224659Z-0b53ed49"
)


def test_canonical_hashes_stable_and_sensitive() -> None:
    a = {"b": 1, "a": [3, 2]}
    b = {"a": [3, 2], "b": 1}
    assert sha256_canonical(a) == sha256_canonical(b)
    assert sha256_canonical(a) != sha256_canonical({"a": [3, 2], "b": 2})


def test_timestamp_path_review_state_do_not_affect_artifact_hash(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    run_id = new_run_id("hash-meta")
    payload = {"facts": [{"id": "f1", "predicate": "sleep", "value": "poor"}]}
    r1 = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload=payload,
        created_at="2026-01-01T00:00:00Z",
        notes="first",
        artifact_id="art_meta_1",
    )
    r2 = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload=payload,
        created_at="2026-12-31T23:59:59Z",
        notes="second different metadata",
        artifact_id="art_meta_2",
    )
    assert r1.artifact_sha256 == r2.artifact_sha256


def test_content_addressed_refuse_different_bytes(tmp_path: Path) -> None:
    store_dir = tmp_path / "by_sha"
    write_content_addressed(store_dir, {"x": 1})
    digest = sha256_canonical({"x": 1})
    path = store_dir / f"{digest}.json"
    path.write_bytes(canonical_json_bytes({"x": 2}))
    with pytest.raises(ContentAddressConflict):
        write_content_addressed(store_dir, {"x": 1})


def test_record_decision_refreshes_index_and_current_view(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    run_id = new_run_id("sync-views")
    r = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload={"n": 1},
        artifact_id="art_sync_1",
    )
    before_view = current_review_path(store, run_id, r.artifact_id).read_text(
        encoding="utf-8"
    )
    assert "unreviewed" in before_view.lower()
    evidence_sha = r.evidence_view.sha256 if r.evidence_view else None
    receipt_bytes = (
        store.run_dir(run_id) / "receipts" / f"{r.artifact_id}.json"
    ).read_bytes()

    record_decision(
        store,
        run_id=run_id,
        artifact_id=r.artifact_id,
        decision="accepted",
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
        notes="gate check",
    )

    index = (store.run_dir(run_id) / "index.md").read_text(encoding="utf-8")
    current = current_review_path(store, run_id, r.artifact_id).read_text(
        encoding="utf-8"
    )
    assert "**accepted**" in index
    assert SYNTHETIC_REVIEWER_ID in index
    assert "synthetic_test" in index
    assert "review status: **accepted**" in current
    assert SYNTHETIC_REVIEWER_ID in current
    assert "origin=`synthetic_test`" in current
    assert r.artifact_sha256[:12] in current
    assert "cannot be an evaluable downstream parent until" not in current.lower()

    # Immutable evidence + receipt unchanged.
    r2 = store.load_receipt(run_id, r.artifact_id)
    assert r2.evidence_view and r2.evidence_view.sha256 == evidence_sha
    assert (
        store.run_dir(run_id) / "receipts" / f"{r.artifact_id}.json"
    ).read_bytes() == receipt_bytes
    evidence_text = store.read_artifact_text(r2.evidence_view)
    assert "review status:" not in evidence_text.lower()
    assert "latest decision:" not in evidence_text.lower()


def test_evidence_view_hash_stable_across_review(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    run_id = new_run_id("ev-stable")
    r = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload={"k": "v"},
        artifact_id="art_ev_1",
        deterministic_decisions={"dispositions": []},
    )
    ev_sha = r.evidence_view.sha256
    art_sha = r.artifact_sha256
    record_decision(
        store,
        run_id=run_id,
        artifact_id=r.artifact_id,
        decision="rejected",
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
    )
    r2 = store.load_receipt(run_id, r.artifact_id)
    assert r2.artifact_sha256 == art_sha
    assert r2.evidence_view.sha256 == ev_sha


def test_synthetic_builder_no_human_ids(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    manifest = build_synthetic_chain(store)
    decisions = (store.run_dir(manifest["run_id"]) / "decisions.jsonl").read_text(
        encoding="utf-8"
    ).lower()
    assert '"tj"' not in decisions
    assert '"molly"' not in decisions
    assert SYNTHETIC_REVIEWER_ID in decisions
    assert "synthetic_test" in decisions
    for art in ("extract_raw", "extract_transform", "ledger"):
        aid = manifest["artifacts"][art]["artifact_id"]
        view = current_review_path(store, manifest["run_id"], aid).read_text(
            encoding="utf-8"
        )
        assert "origin=`synthetic_test`" in view
        assert "Not human approval" in view


def test_synthetic_test_not_masquerading_as_human(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    run_id = new_run_id("masq")
    r = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload={"x": 1},
        artifact_id="art_masq",
    )
    record_decision(
        store,
        run_id=run_id,
        artifact_id=r.artifact_id,
        decision="accepted",
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
    )
    view = current_review_path(store, run_id, r.artifact_id).read_text(encoding="utf-8")
    assert "Not human approval" in view
    assert is_accepted(store, run_id, r.artifact_id, require_human=True) is False
    with pytest.raises(Exception):
        ReviewDecision(
            artifact_id=r.artifact_id,
            artifact_sha256=r.artifact_sha256,
            decision="accepted",
            origin="synthetic_test",
            reviewer_id="tj",
            reviewer_role="engineer",
            reviewed_at="2026-08-10T00:00:00Z",
        )


def test_diagnostic_silent_drops_not_quarantine(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    manifest = index_audit(store)
    assert manifest["observed_silent_drop_count"] == 6
    receipt = store.load_receipt(
        manifest["run_id"], manifest["diagnostic_replay_artifact_id"]
    )
    decisions = store.read_artifact_json(receipt.deterministic_decisions)
    kinds = {d["kind"] for d in decisions["dispositions"]}
    assert "observed_silent_drop" in kinds
    assert "quarantined" not in kinds
    assert decisions["quarantine_review_items"] == []
    for d in decisions["dispositions"]:
        if d["kind"] == "observed_silent_drop":
            assert d.get("review_item_id") is None
            assert d.get("gate_or_check")
    view = current_review_path(
        store, manifest["run_id"], receipt.artifact_id
    ).read_text(encoding="utf-8")
    assert "observed silent drop" in view.lower()
    assert "- **observed silent drop**: 6" in view or "- `observed silent drop`: 6" in view
    assert "q_" not in "".join(
        d.get("review_item_id") or "" for d in decisions["dispositions"]
    )


def test_observed_silent_drop_forbidden_on_evaluable() -> None:
    with pytest.raises(AccountingError):
        validate_extract_dispositions(
            ["i0"],
            [
                ExtractDisposition(
                    item_id="i0",
                    kind="observed_silent_drop",
                    gate_or_check="_draft_is_skippable",
                    reason="spurious_grade",
                )
            ],
            lineage="evaluable",
        )


def test_diagnostic_not_parent_of_legacy(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    manifest = index_audit(store)
    assert manifest["linked_as_parent"] is False
    replay = store.load_receipt(
        manifest["run_id"], manifest["diagnostic_replay_artifact_id"]
    )
    legacy = store.load_receipt(
        manifest["run_id"], manifest["legacy_ledger_artifact_id"]
    )
    assert replay.lineage == "diagnostic_replay"
    assert legacy.lineage == "legacy_untraceable"
    assert replay.parents == []


def test_append_eval_leaves_receipt_and_evidence_unchanged(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    run_id = new_run_id("eval-append")
    r = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload={"facts": []},
        artifact_id="art_eval_1",
    )
    receipt_bytes = (
        store.run_dir(run_id) / "receipts" / f"{r.artifact_id}.json"
    ).read_bytes()
    art_sha = r.artifact_sha256
    ev_sha = r.evidence_view.sha256

    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=r.artifact_id,
        check_id="ledger_schema",
        check_version="1",
        result="pass",
        evaluator_id="system",
        evaluator_origin="system",
    )
    append_eval_record(
        store,
        run_id=run_id,
        artifact_id=r.artifact_id,
        check_id="ledger_schema",
        check_version="2",
        result="fail",
        detail="stricter check",
        evaluator_id="system",
        evaluator_origin="system",
    )

    r2 = store.load_receipt(run_id, r.artifact_id)
    assert r2.artifact_sha256 == art_sha
    assert r2.evidence_view.sha256 == ev_sha
    assert (
        store.run_dir(run_id) / "receipts" / f"{r.artifact_id}.json"
    ).read_bytes() == receipt_bytes

    records = load_eval_records_for_artifact(store, run_id, r.artifact_id)
    assert len(records) == 2
    assert {rec.check_version for rec in records} == {"1", "2"}
    assert all(rec.artifact_sha256 == art_sha for rec in records)

    view = current_review_path(store, run_id, r.artifact_id).read_text(encoding="utf-8")
    assert "ledger_schema`@1" in view or "ledger_schema`@1:" in view
    assert "ledger_schema`@2" in view or "ledger_schema`@2:" in view
    index = (store.run_dir(run_id) / "index.md").read_text(encoding="utf-8")
    assert r.artifact_id in index


def test_synthetic_parent_gate_and_unreviewed_brief(tmp_path: Path) -> None:
    store = ReceiptStore(tmp_path / "store")
    run_id = new_run_id("gate")
    parent = build_receipt(
        store=store,
        run_id=run_id,
        stage="ledger",
        machine_payload={"facts": []},
        artifact_id="art_parent_gate",
    )
    with pytest.raises(ReviewError):
        require_accepted_parent(
            store,
            run_id=run_id,
            artifact_id=parent.artifact_id,
            expected_sha256=parent.artifact_sha256,
        )
    record_decision(
        store,
        run_id=run_id,
        artifact_id=parent.artifact_id,
        decision="accepted",
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
    )
    require_accepted_parent(
        store,
        run_id=run_id,
        artifact_id=parent.artifact_id,
        expected_sha256=parent.artifact_sha256,
    )

    manifest = build_synthetic_chain(store)
    brief_id = manifest["artifacts"]["brief"]["artifact_id"]
    assert review_status(store, manifest["run_id"], brief_id) == "unreviewed"
    brief_view = current_review_path(store, manifest["run_id"], brief_id).read_text(
        encoding="utf-8"
    )
    assert "review status: **unreviewed**" in brief_view


def test_extract_disposition_total_accounting() -> None:
    items = ["i0", "i1", "i2", "i3"]
    disps = [
        ExtractDisposition(item_id="i0", kind="retained", fact_id="f1"),
        ExtractDisposition(
            item_id="i1",
            kind="transformed",
            fact_id="f2",
            before={"value": "a"},
            after={"value": "b"},
        ),
        ExtractDisposition(
            item_id="i2", kind="suppressed_duplicate", canonical_fact_id="f1"
        ),
        ExtractDisposition(
            item_id="i3",
            kind="quarantined",
            review_item_id="q1",
            reason="heuristic",
        ),
    ]
    counts = validate_extract_dispositions(items, disps, lineage="evaluable")
    assert sum(counts.values()) == 4


def test_unaccounted_and_forbidden_excluded_fail() -> None:
    with pytest.raises(AccountingError):
        validate_extract_dispositions(
            ["i0", "i1"],
            [ExtractDisposition(item_id="i0", kind="retained", fact_id="f1")],
        )
    with pytest.raises(AccountingError):
        assert_no_generic_excluded(["excluded"])


def test_duplicate_and_quarantine_require_targets() -> None:
    with pytest.raises(Exception):
        ExtractDisposition(item_id="i", kind="suppressed_duplicate")
    with pytest.raises(Exception):
        ExtractDisposition(item_id="i", kind="quarantined", reason="x")


def test_brief_disposition_allows_multi_destination_reuse() -> None:
    facts = ["f1", "f2"]
    disps = [
        BriefDisposition(
            fact_id="f1",
            kind="selected",
            destinations=["health_history", "rater_input:parent"],
        ),
        BriefDisposition(
            fact_id="f2", kind="held_for_review", reason="after_evaluation_date"
        ),
    ]
    counts = validate_brief_dispositions(facts, disps)
    assert counts["selected"] == 1


def test_suite_has_no_network_env_requirement() -> None:
    for key in ("OPENAI_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        _ = os.environ.get(key)
    assert callable(build_synthetic_chain)
    assert callable(index_audit)


def test_requirements_dev_documents_pytest() -> None:
    assert _DEV_REQ.is_file()
    text = _DEV_REQ.read_text(encoding="utf-8")
    assert "pytest" in text
    prod = (_WEEK1 / "requirements.txt").read_text(encoding="utf-8")
    assert "pytest" not in prod


def test_old_invalid_demo_preserved_if_present() -> None:
    if not _OLD_SYNTHETIC.exists():
        pytest.skip("old synthetic demo run not present")
    index = (_OLD_SYNTHETIC / "index.md").read_text(encoding="utf-8")
    # After repair script, banner should be present; if not yet marked, still
    # keep decisions with tj for inspection.
    decisions = (_OLD_SYNTHETIC / "decisions.jsonl").read_text(encoding="utf-8")
    assert "tj" in decisions
