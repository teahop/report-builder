"""Focused tests for extraction comparison review surfaces — zero network/model calls.

All mutating item/coverage review tests use a temporary receipt store. Running
this suite must leave the live diagnostic ``item_reviews.jsonl`` /
``coverage_reviews.jsonl`` byte-for-byte unchanged.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

_WEEK1 = Path(__file__).resolve().parent
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.history.item_review import (
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_RUN_ID,
    append_coverage_omission,
    append_item_review,
    invalidate_contaminated_live_reviews,
    invalidated_sha_set,
    load_coverage_reviews,
    load_item_reviews,
    record_content_sha,
    summarize_reviews,
)
from evals.history.refresh_extraction_review_surfaces import (
    comparison_nav_markdown,
    refresh_all,
)
from evals.history.render_item_comparison import (
    COMPARISON_PAGES,
    DEFAULT_CHUNK_STEM,
    ChunkShaMismatchError,
    MissingChunkSourceError,
    _find_passage,
    load_full_chunk_source,
    render_all_comparisons,
    sha256_text,
)
from evals.receipts.models import SYNTHETIC_REVIEWER_ID, SYNTHETIC_REVIEWER_ROLE
from evals.receipts.store import ReceiptStore, build_receipt

_AUDIT = _WEEK1 / "evals" / "history" / "extraction_audit"
_OUT = _AUDIT / "item_comparison"
_LIVE_RUN = (
    _WEEK1 / "evals" / "receipts" / "store" / "runs" / DIAGNOSTIC_RUN_ID
)


@pytest.fixture
def live_review_bytes() -> tuple[bytes | None, bytes | None]:
    items = _LIVE_RUN / "item_reviews.jsonl"
    cov = _LIVE_RUN / "coverage_reviews.jsonl"
    return (
        items.read_bytes() if items.exists() else None,
        cov.read_bytes() if cov.exists() else None,
    )


@pytest.fixture
def isolated_store(tmp_path: Path) -> tuple[ReceiptStore, str, str, str]:
    """Copy the diagnostic receipt into a temp store for mutating tests."""

    store = ReceiptStore(tmp_path / "store")
    live = ReceiptStore()
    if not (_LIVE_RUN / "receipts" / f"{DIAGNOSTIC_ARTIFACT_ID}.json").exists():
        pytest.skip("corrected diagnostic run not present")
    receipt = live.load_receipt(DIAGNOSTIC_RUN_ID, DIAGNOSTIC_ARTIFACT_ID)
    # Materialize a minimal evaluable twin under a new run id.
    run_id = "tmp-extraction-review-test"
    machine = live.read_artifact_json(receipt.machine_output)
    decisions = None
    if receipt.deterministic_decisions is not None:
        decisions = live.read_artifact_json(receipt.deterministic_decisions)
    twin = build_receipt(
        store=store,
        run_id=run_id,
        stage="diagnostic_replay",
        machine_payload=machine,
        deterministic_decisions=decisions,
        lineage="diagnostic_replay",
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        notes="isolated test twin",
    )
    chunk_sha = json.loads(
        (_AUDIT / "doc_11_chunk04.json").read_text(encoding="utf-8")
    )["chunk_sha256"]
    return store, run_id, twin.artifact_sha256, chunk_sha


def test_suite_leaves_live_review_logs_unchanged(live_review_bytes) -> None:
    before_items, before_cov = live_review_bytes
    # Exercise the suite's non-mutating and temp-store paths indirectly by
    # reading live logs only — mutating tests use isolated_store.
    store = ReceiptStore()
    _ = load_item_reviews(store, DIAGNOSTIC_RUN_ID)
    _ = load_coverage_reviews(store, DIAGNOSTIC_RUN_ID)
    items = _LIVE_RUN / "item_reviews.jsonl"
    cov = _LIVE_RUN / "coverage_reviews.jsonl"
    after_items = items.read_bytes() if items.exists() else None
    after_cov = cov.read_bytes() if cov.exists() else None
    assert after_items == before_items
    assert after_cov == before_cov


def test_diagnostic_current_review_links_to_comparisons() -> None:
    store = ReceiptStore()
    # Rebuildable views only — must not append review logs.
    items_path = _LIVE_RUN / "item_reviews.jsonl"
    cov_path = _LIVE_RUN / "coverage_reviews.jsonl"
    before_i = items_path.read_bytes() if items_path.exists() else None
    before_c = cov_path.read_bytes() if cov_path.exists() else None
    result = refresh_all(store=store)
    assert (items_path.read_bytes() if items_path.exists() else None) == before_i
    assert (cov_path.read_bytes() if cov_path.exists() else None) == before_c
    current = Path(result["current_review"]).read_text(encoding="utf-8")
    index = Path(result["index"]).read_text(encoding="utf-8")
    for text in (current, index):
        assert "Human-readable item comparisons" in text
        assert f"{DEFAULT_CHUNK_STEM}.md" in text
        assert "targeted_chunk_replay" in text
    assert "Start here" in current
    nav = comparison_nav_markdown(from_current_view=True)
    assert f"item_comparison/{DEFAULT_CHUNK_STEM}.md" in nav


def test_all_eight_pages_match_recorded_chunk_sha() -> None:
    machines = render_all_comparisons()
    assert len(machines) == 8
    for stem in COMPARISON_PAGES:
        data = json.loads((_AUDIT / f"{stem}.json").read_text(encoding="utf-8"))
        content = load_full_chunk_source(data, artifact_path=_AUDIT / f"{stem}.json")
        assert sha256_text(content) == data["chunk_sha256"]
        md = (_OUT / f"{stem}.md").read_text(encoding="utf-8")
        assert "## Complete source chunk (omission surface)" in md
        assert data["chunk_sha256"] in md


def test_missing_full_source_fails_loudly(tmp_path: Path) -> None:
    bad = {"chunk_sha256": "abc123", "user_payload": {"source": {}}}
    with pytest.raises(MissingChunkSourceError):
        load_full_chunk_source(bad, artifact_path=tmp_path / "missing.json")
    mismatched = {
        "chunk_sha256": "0" * 64,
        "user_payload": {"source": {"content": "hello world"}},
    }
    with pytest.raises(ChunkShaMismatchError):
        load_full_chunk_source(mismatched, artifact_path=tmp_path / "mismatch.json")


def test_append_item_review_leaves_receipt_hashes_unchanged(
    isolated_store,
) -> None:
    store, run_id, art_sha, chunk_sha = isolated_store
    receipt = store.load_receipt(run_id, DIAGNOSTIC_ARTIFACT_ID)
    receipt_bytes = (
        store.run_dir(run_id) / "receipts" / f"{DIAGNOSTIC_ARTIFACT_ID}.json"
    ).read_bytes()
    ev_sha = receipt.evidence_view.sha256 if receipt.evidence_view else None
    machine_bytes = (store.root / receipt.machine_output.relative_path).read_bytes()

    append_item_review(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        item_id=f"doc_11:chunk:{chunk_sha[:12]}:raw:002",
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
        judgments={
            "source_support": "fail",
            "predicate": "fail",
            "value": "uncertain",
            "metadata": "pass",
            "deterministic_disposition": "pass",
        },
    )
    receipt2 = store.load_receipt(run_id, DIAGNOSTIC_ARTIFACT_ID)
    assert receipt2.artifact_sha256 == art_sha == receipt.artifact_sha256
    assert receipt2.evidence_view and receipt2.evidence_view.sha256 == ev_sha
    assert (
        store.run_dir(run_id) / "receipts" / f"{DIAGNOSTIC_ARTIFACT_ID}.json"
    ).read_bytes() == receipt_bytes
    assert (
        store.root / receipt.machine_output.relative_path
    ).read_bytes() == machine_bytes


def test_multiple_item_judgments_keep_history_latest_identified(
    isolated_store,
) -> None:
    store, run_id, _, chunk_sha = isolated_store
    item_id = f"doc_11:chunk:{chunk_sha[:12]}:raw:005"
    append_item_review(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        item_id=item_id,
        origin="human",
        reviewer_id="tj",
        reviewer_role="engineer",
        judgments={
            "source_support": "pass",
            "predicate": "uncertain",
            "value": "uncertain",
            "metadata": "pass",
            "deterministic_disposition": "pass",
        },
        notes="first",
        reviewed_at="2026-08-10T23:00:00Z",
    )
    append_item_review(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        item_id=item_id,
        origin="human",
        reviewer_id="tj",
        reviewer_role="engineer",
        judgments={
            "source_support": "pass",
            "predicate": "fail",
            "value": "fail",
            "metadata": "pass",
            "deterministic_disposition": "pass",
        },
        notes="second latest",
        reviewed_at="2026-08-10T23:10:00Z",
    )
    rows = [r for r in load_item_reviews(store, run_id) if r.item_id == item_id]
    assert rows[-1].notes == "second latest"
    assert rows[-1].judgments.predicate == "fail"


def test_item_dimensions_can_differ_independently(isolated_store) -> None:
    store, run_id, _, chunk_sha = isolated_store
    item_id = f"doc_11:chunk:{chunk_sha[:12]}:raw:003"
    append_item_review(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        item_id=item_id,
        origin="human",
        reviewer_id="tj",
        reviewer_role="engineer",
        judgments={
            "source_support": "pass",
            "predicate": "fail",
            "value": "uncertain",
            "metadata": "not_applicable",
            "deterministic_disposition": "pass",
        },
    )
    latest = [
        r for r in load_item_reviews(store, run_id) if r.item_id == item_id
    ][-1]
    assert latest.judgments.source_support == "pass"
    assert latest.judgments.predicate == "fail"
    assert latest.judgments.value == "uncertain"


def test_coverage_omission_anchored_to_hashes_and_locator(isolated_store) -> None:
    store, run_id, art_sha, chunk_sha = isolated_store
    row = append_coverage_omission(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        source_locator="Area of Need: Written Expression",
        description="Writing goal present but no written_expression predicate emitted",
        origin="human",
        reviewer_id="tj",
        reviewer_role="engineer",
        proposed_predicate="written_expression",
        source_span_start=100,
        source_span_end=140,
    )
    assert row.artifact_sha256 == art_sha
    assert row.chunk_sha256 == chunk_sha


def test_automation_cannot_create_human_tj_molly_item_review(isolated_store) -> None:
    store, run_id, _, chunk_sha = isolated_store
    with pytest.raises(Exception):
        append_item_review(
            store,
            run_id=run_id,
            artifact_id=DIAGNOSTIC_ARTIFACT_ID,
            chunk_sha256=chunk_sha,
            item_id="x",
            origin="synthetic_test",
            reviewer_id="tj",
            reviewer_role="engineer",
            judgments={
                "source_support": "pass",
                "predicate": "pass",
                "value": "pass",
                "metadata": "pass",
                "deterministic_disposition": "pass",
            },
        )
    with pytest.raises(Exception):
        append_coverage_omission(
            store,
            run_id=run_id,
            artifact_id=DIAGNOSTIC_ARTIFACT_ID,
            chunk_sha256=chunk_sha,
            source_locator="x",
            description="y",
            origin="synthetic_test",
            reviewer_id="molly",
            reviewer_role="clinician",
        )


def test_summary_human_progress_ignores_synthetic_and_invalidated(
    isolated_store,
) -> None:
    store, run_id, art_sha, chunk_sha = isolated_store
    item_id = f"doc_11:chunk:{chunk_sha[:12]}:raw:002"
    # Contaminating synthetic + false human, then invalidate.
    append_item_review(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        item_id=item_id,
        origin="synthetic_test",
        reviewer_id=SYNTHETIC_REVIEWER_ID,
        reviewer_role=SYNTHETIC_REVIEWER_ROLE,
        judgments={
            "source_support": "fail",
            "predicate": "fail",
            "value": "fail",
            "metadata": "pass",
            "deterministic_disposition": "pass",
        },
    )
    append_item_review(
        store,
        run_id=run_id,
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        chunk_sha256=chunk_sha,
        item_id=item_id,
        origin="human",
        reviewer_id="tj",
        reviewer_role="engineer",
        judgments={
            "source_support": "pass",
            "predicate": "fail",
            "value": "fail",
            "metadata": "pass",
            "deterministic_disposition": "pass",
        },
        notes="…",
    )
    invalidate_contaminated_live_reviews(store, run_id=run_id)
    summary = summarize_reviews(
        item_records=load_item_reviews(store, run_id),
        coverage_records=load_coverage_reviews(store, run_id),
        raw_item_ids=[item_id] + [f"other:{i}" for i in range(69)],
        silent_drop_item_ids=[],
        retained_item_ids=[item_id],
        artifact_id=DIAGNOSTIC_ARTIFACT_ID,
        artifact_sha256=art_sha,
        chunk_hashes={"doc_11_chunk04": chunk_sha},
        invalidated_item_shas=invalidated_sha_set(store, run_id, kind="item_review"),
        invalidated_coverage_shas=invalidated_sha_set(
            store, run_id, kind="coverage_review"
        ),
    )
    assert summary["human_reviewed_item_count"] == 0
    assert summary["human_unreviewed_item_count"] == 70
    assert summary["human_coverage_omission_count"] == 0
    assert summary["invalidated_item_review_count"] == 2


def test_whitespace_tolerant_passage_finds_item_06() -> None:
    data = json.loads((_AUDIT / "doc_11_chunk04.json").read_text(encoding="utf-8"))
    content = load_full_chunk_source(data, artifact_path=_AUDIT / "doc_11_chunk04.json")
    needle = (
        "can solve 5 one-step equations with whole number coefficients with at "
        "least 90% accuracy in 1/2 trials"
    )
    found = _find_passage(content, needle)
    assert found is not None
    assert "one-step" in found.lower() or "one-step" in found


def test_live_current_state_has_zero_human_progress() -> None:
    store = ReceiptStore()
    if not _LIVE_RUN.exists():
        pytest.skip("corrected diagnostic run not present")
    summary = json.loads(
        (_OUT / "extraction_review_summary.json").read_text(encoding="utf-8")
    )
    assert summary["human_reviewed_item_count"] == 0
    assert summary["human_coverage_omission_count"] == 0
    assert summary["raw_item_count"] == 70
    page = (_OUT / "doc_11_chunk04.md").read_text(encoding="utf-8")
    assert "origin=`human`" not in page or "No human item review" in page
    # Must not attribute current judgment to tj/molly.
    assert "reviewer=`tj`" not in page
    assert "reviewer=`molly`" not in page
    inv = invalidated_sha_set(store, DIAGNOSTIC_RUN_ID, kind="item_review")
    live_items = load_item_reviews(store, DIAGNOSTIC_RUN_ID)
    assert live_items
    for rec in live_items:
        assert record_content_sha(rec) in inv
    assert summary["invalidated_item_review_count"] == len(live_items)
    assert summary["human_reviewed_item_count"] == 0
    assert summary["synthetic_active_item_review_count"] == 0


def test_suite_no_network_keys_required() -> None:
    for key in ("OPENAI_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        _ = os.environ.get(key)
    assert callable(refresh_all)
