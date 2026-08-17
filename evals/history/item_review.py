"""Append-only item and chunk-coverage review records for extraction audit (eval-only).

Does not mutate stage receipts, machine artifacts, or immutable evidence views.
Makes zero model calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, model_validator

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.receipts.models import (  # noqa: E402
    FORBIDDEN_AUTO_HUMAN_IDS,
    SYNTHETIC_REVIEWER_ID,
    SYNTHETIC_REVIEWER_ROLE,
    DecisionOrigin,
)
from evals.receipts.store import ReceiptStore  # noqa: E402

ITEM_REVIEW_VERSION = "1"
COVERAGE_REVIEW_VERSION = "1"
INVALIDATION_VERSION = "1"

DimensionStatus = Literal["pass", "fail", "uncertain", "not_applicable"]
ITEM_DIMENSIONS = (
    "source_support",
    "predicate",
    "value",
    "metadata",
    "deterministic_disposition",
)

DIAGNOSTIC_RUN_ID = "extract-audit-replay-20260810T231331Z-6b58509e"
DIAGNOSTIC_ARTIFACT_ID = "art_extract_audit_replay_v2"


class ItemReviewError(ValueError):
    """Invalid item/coverage review record."""


class ItemDimensionJudgments(BaseModel):
    source_support: DimensionStatus
    predicate: DimensionStatus
    value: DimensionStatus
    metadata: DimensionStatus
    deterministic_disposition: DimensionStatus


class ItemReviewRecord(BaseModel):
    record_version: str = ITEM_REVIEW_VERSION
    artifact_id: str
    artifact_sha256: str
    chunk_sha256: str
    item_id: str
    origin: DecisionOrigin
    reviewer_id: str
    reviewer_role: str
    reviewed_at: str
    judgments: ItemDimensionJudgments
    notes: str = ""

    @model_validator(mode="after")
    def _identity(self) -> ItemReviewRecord:
        _validate_reviewer_identity(self.origin, self.reviewer_id, self.reviewer_role)
        return self


class CoverageOmissionRecord(BaseModel):
    record_version: str = COVERAGE_REVIEW_VERSION
    artifact_id: str
    artifact_sha256: str
    chunk_sha256: str
    source_locator: str
    source_span_start: int | None = None
    source_span_end: int | None = None
    description: str
    proposed_predicate: str | None = None
    proposed_predicate_provisional: bool = True
    origin: DecisionOrigin
    reviewer_id: str
    reviewer_role: str
    reviewed_at: str
    notes: str = ""

    @model_validator(mode="after")
    def _identity_and_locator(self) -> CoverageOmissionRecord:
        _validate_reviewer_identity(self.origin, self.reviewer_id, self.reviewer_role)
        if not self.source_locator.strip():
            raise ValueError("coverage omission requires a source_locator")
        if not self.description.strip():
            raise ValueError("coverage omission requires a description")
        return self


def _validate_reviewer_identity(
    origin: str, reviewer_id: str, reviewer_role: str
) -> None:
    rid = reviewer_id.strip().lower()
    if origin == "synthetic_test":
        if rid in FORBIDDEN_AUTO_HUMAN_IDS:
            raise ItemReviewError(
                f"synthetic_test must not use human identity {reviewer_id!r}"
            )
        if rid != SYNTHETIC_REVIEWER_ID:
            raise ItemReviewError(
                f"synthetic_test reviewer_id must be {SYNTHETIC_REVIEWER_ID!r}"
            )
        if reviewer_role != SYNTHETIC_REVIEWER_ROLE:
            raise ItemReviewError(
                f"synthetic_test reviewer_role must be {SYNTHETIC_REVIEWER_ROLE!r}"
            )
    if origin == "human" and rid == SYNTHETIC_REVIEWER_ID:
        raise ItemReviewError("human origin cannot use receipt_test_harness identity")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_content_sha(obj: BaseModel | dict[str, Any]) -> str:
    """Stable SHA of a review row's JSON (for append-only invalidation)."""

    if isinstance(obj, BaseModel):
        payload = obj.model_dump(mode="json")
    else:
        payload = obj
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ReviewInvalidationRecord(BaseModel):
    """Append-only invalidation — does not delete or rewrite prior review rows."""

    invalidation_version: str = INVALIDATION_VERSION
    target_kind: Literal["item_review", "coverage_review"]
    record_sha256: str
    reason: str
    invalidated_at: str
    invalidated_by: str = "system_correction"
    notes: str = ""


def item_reviews_path(store: ReceiptStore, run_id: str) -> Path:
    return store.run_dir(run_id) / "item_reviews.jsonl"


def coverage_reviews_path(store: ReceiptStore, run_id: str) -> Path:
    return store.run_dir(run_id) / "coverage_reviews.jsonl"


def invalidations_path(store: ReceiptStore, run_id: str) -> Path:
    return store.run_dir(run_id) / "review_invalidations.jsonl"


def load_item_reviews(store: ReceiptStore, run_id: str) -> list[ItemReviewRecord]:
    path = item_reviews_path(store, run_id)
    if not path.exists():
        return []
    out: list[ItemReviewRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(ItemReviewRecord.model_validate_json(line))
    return out


def load_coverage_reviews(
    store: ReceiptStore, run_id: str
) -> list[CoverageOmissionRecord]:
    path = coverage_reviews_path(store, run_id)
    if not path.exists():
        return []
    out: list[CoverageOmissionRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(CoverageOmissionRecord.model_validate_json(line))
    return out


def load_invalidations(
    store: ReceiptStore, run_id: str
) -> list[ReviewInvalidationRecord]:
    path = invalidations_path(store, run_id)
    if not path.exists():
        return []
    out: list[ReviewInvalidationRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(ReviewInvalidationRecord.model_validate_json(line))
    return out


def invalidated_sha_set(
    store: ReceiptStore, run_id: str, *, kind: str | None = None
) -> set[str]:
    out: set[str] = set()
    for inv in load_invalidations(store, run_id):
        if kind is None or inv.target_kind == kind:
            out.add(inv.record_sha256)
    return out


def append_invalidation(
    store: ReceiptStore,
    *,
    run_id: str,
    target_kind: str,
    record_sha256: str,
    reason: str,
    notes: str = "",
    invalidated_at: str | None = None,
    invalidated_by: str = "system_correction",
) -> ReviewInvalidationRecord:
    row = ReviewInvalidationRecord(
        target_kind=target_kind,  # type: ignore[arg-type]
        record_sha256=record_sha256,
        reason=reason,
        invalidated_at=invalidated_at or utc_now(),
        invalidated_by=invalidated_by,
        notes=notes,
    )
    path = invalidations_path(store, run_id)
    # Idempotent: identical invalidation may rewrite; divergent same-sha notes OK to skip.
    existing = {i.record_sha256 for i in load_invalidations(store, run_id)
                if i.target_kind == target_kind}
    if record_sha256 in existing:
        return row
    with path.open("a", encoding="utf-8") as fh:
        fh.write(row.model_dump_json() + "\n")
    return row


def invalidate_contaminated_live_reviews(
    store: ReceiptStore,
    *,
    run_id: str = DIAGNOSTIC_RUN_ID,
) -> dict[str, int]:
    """
    Mark every existing contaminated live review row as invalid test/demo history.

    Preserves the original JSONL rows. Appends invalidation records only.
    """

    item_n = 0
    for rec in load_item_reviews(store, run_id):
        sha = record_content_sha(rec)
        if rec.origin == "human":
            reason = "fabricated_or_unverified_human_identity"
            notes = (
                "Row claimed human/TJ review before TJ supplied a judgment. "
                "Invalidated; does not count as human progress."
            )
        else:
            reason = "focused_test_wrote_to_live_diagnostic_run"
            notes = (
                "Synthetic harness / focused-test row written into the live "
                "diagnostic run. Auditable test evidence only."
            )
        append_invalidation(
            store,
            run_id=run_id,
            target_kind="item_review",
            record_sha256=sha,
            reason=reason,
            notes=notes,
        )
        item_n += 1

    cov_n = 0
    for rec in load_coverage_reviews(store, run_id):
        sha = record_content_sha(rec)
        append_invalidation(
            store,
            run_id=run_id,
            target_kind="coverage_review",
            record_sha256=sha,
            reason="focused_test_wrote_to_live_diagnostic_run",
            notes=(
                "Synthetic harness / focused-test coverage row on the live "
                "diagnostic run. Auditable test evidence only."
            ),
        )
        cov_n += 1
    return {"item_invalidations": item_n, "coverage_invalidations": cov_n}


def latest_item_review(
    records: list[ItemReviewRecord],
    item_id: str,
    *,
    invalidated: set[str] | None = None,
    origin: str | None = None,
) -> ItemReviewRecord | None:
    """Latest non-invalidated review for an item; optionally filter by origin."""

    latest: ItemReviewRecord | None = None
    inv = invalidated or set()
    for r in records:
        if r.item_id != item_id:
            continue
        if record_content_sha(r) in inv:
            continue
        if origin is not None and r.origin != origin:
            continue
        latest = r
    return latest


def active_item_reviews(
    records: list[ItemReviewRecord], *, invalidated: set[str]
) -> list[ItemReviewRecord]:
    return [r for r in records if record_content_sha(r) not in invalidated]


def active_coverage_reviews(
    records: list[CoverageOmissionRecord], *, invalidated: set[str]
) -> list[CoverageOmissionRecord]:
    return [r for r in records if record_content_sha(r) not in invalidated]


def append_item_review(
    store: ReceiptStore,
    *,
    run_id: str,
    artifact_id: str,
    chunk_sha256: str,
    item_id: str,
    origin: str,
    reviewer_id: str,
    reviewer_role: str,
    judgments: dict[str, str],
    notes: str = "",
    reviewed_at: str | None = None,
    expected_sha256: str | None = None,
) -> ItemReviewRecord:
    receipt = store.load_receipt(run_id, artifact_id)
    sha = expected_sha256 or receipt.artifact_sha256
    if sha != receipt.artifact_sha256:
        raise ItemReviewError(
            f"artifact SHA mismatch: expected {sha[:12]} got "
            f"{receipt.artifact_sha256[:12]}"
        )
    row = ItemReviewRecord(
        artifact_id=artifact_id,
        artifact_sha256=sha,
        chunk_sha256=chunk_sha256,
        item_id=item_id,
        origin=origin,  # type: ignore[arg-type]
        reviewer_id=reviewer_id,
        reviewer_role=reviewer_role,
        reviewed_at=reviewed_at or utc_now(),
        judgments=ItemDimensionJudgments.model_validate(judgments),
        notes=notes,
    )
    path = item_reviews_path(store, run_id)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(row.model_dump_json() + "\n")
    return row


def append_coverage_omission(
    store: ReceiptStore,
    *,
    run_id: str,
    artifact_id: str,
    chunk_sha256: str,
    source_locator: str,
    description: str,
    origin: str,
    reviewer_id: str,
    reviewer_role: str,
    proposed_predicate: str | None = None,
    proposed_predicate_provisional: bool = True,
    source_span_start: int | None = None,
    source_span_end: int | None = None,
    notes: str = "",
    reviewed_at: str | None = None,
    expected_sha256: str | None = None,
) -> CoverageOmissionRecord:
    receipt = store.load_receipt(run_id, artifact_id)
    sha = expected_sha256 or receipt.artifact_sha256
    if sha != receipt.artifact_sha256:
        raise ItemReviewError(
            f"artifact SHA mismatch: expected {sha[:12]} got "
            f"{receipt.artifact_sha256[:12]}"
        )
    row = CoverageOmissionRecord(
        artifact_id=artifact_id,
        artifact_sha256=sha,
        chunk_sha256=chunk_sha256,
        source_locator=source_locator,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        description=description,
        proposed_predicate=proposed_predicate,
        proposed_predicate_provisional=proposed_predicate_provisional,
        origin=origin,  # type: ignore[arg-type]
        reviewer_id=reviewer_id,
        reviewer_role=reviewer_role,
        reviewed_at=reviewed_at or utc_now(),
        notes=notes,
    )
    path = coverage_reviews_path(store, run_id)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(row.model_dump_json() + "\n")
    return row


def summarize_reviews(
    *,
    item_records: list[ItemReviewRecord],
    coverage_records: list[CoverageOmissionRecord],
    raw_item_ids: list[str],
    silent_drop_item_ids: list[str],
    retained_item_ids: list[str],
    artifact_id: str,
    artifact_sha256: str,
    chunk_hashes: dict[str, str],
    invalidated_item_shas: set[str] | None = None,
    invalidated_coverage_shas: set[str] | None = None,
) -> dict[str, Any]:
    """Build machine summary totals. Main progress counts are human-only."""

    inv_items = invalidated_item_shas or set()
    inv_cov = invalidated_coverage_shas or set()

    scoped_items = [
        r
        for r in item_records
        if r.artifact_id == artifact_id and r.artifact_sha256 == artifact_sha256
    ]
    scoped_cov = [
        c
        for c in coverage_records
        if c.artifact_id == artifact_id and c.artifact_sha256 == artifact_sha256
    ]

    active_human: list[ItemReviewRecord] = []
    active_synthetic: list[ItemReviewRecord] = []
    invalidated_items: list[ItemReviewRecord] = []
    for r in scoped_items:
        if record_content_sha(r) in inv_items:
            invalidated_items.append(r)
            continue
        if r.origin == "human":
            active_human.append(r)
        else:
            active_synthetic.append(r)

    latest_human: dict[str, ItemReviewRecord] = {}
    for r in active_human:
        latest_human[r.item_id] = r

    reviewed_ids = set(latest_human) & set(raw_item_ids)
    unreviewed = [i for i in raw_item_ids if i not in reviewed_ids]

    dim_counts: dict[str, dict[str, int]] = {
        d: {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
        for d in ITEM_DIMENSIONS
    }
    for item_id, rec in latest_human.items():
        if item_id not in raw_item_ids:
            continue
        for dim in ITEM_DIMENSIONS:
            status = getattr(rec.judgments, dim)
            dim_counts[dim][status] += 1

    problem_retained: list[dict[str, Any]] = []
    for item_id in retained_item_ids:
        rec = latest_human.get(item_id)
        if rec is None:
            continue
        bad = {
            d: getattr(rec.judgments, d)
            for d in ("source_support", "predicate", "value")
            if getattr(rec.judgments, d) in {"fail", "uncertain"}
        }
        if bad:
            problem_retained.append(
                {
                    "item_id": item_id,
                    "chunk_sha256": rec.chunk_sha256,
                    "dimensions": bad,
                    "notes": rec.notes,
                    "origin": rec.origin,
                    "reviewer_id": rec.reviewer_id,
                }
            )

    active_human_omissions = [
        c.model_dump(mode="json")
        for c in scoped_cov
        if record_content_sha(c) not in inv_cov and c.origin == "human"
    ]
    active_synthetic_omissions = [
        c.model_dump(mode="json")
        for c in scoped_cov
        if record_content_sha(c) not in inv_cov and c.origin == "synthetic_test"
    ]
    invalidated_omissions = [
        c.model_dump(mode="json")
        for c in scoped_cov
        if record_content_sha(c) in inv_cov
    ]

    return {
        "artifact_id": artifact_id,
        "artifact_sha256": artifact_sha256,
        "chunk_hashes": chunk_hashes,
        "raw_item_count": len(raw_item_ids),
        # Human-only progress (what TJ sees as current review state).
        "human_reviewed_item_count": len(reviewed_ids),
        "human_unreviewed_item_count": len(unreviewed),
        "human_unreviewed_item_ids": unreviewed,
        "human_coverage_omission_count": len(active_human_omissions),
        "human_dimension_counts": dim_counts,
        "human_retained_with_failed_or_uncertain_support_predicate_or_value": problem_retained,
        "human_coverage_omissions": active_human_omissions,
        # Synthetic / invalid — never counted as content-review progress.
        "synthetic_active_item_review_count": len(active_synthetic),
        "synthetic_active_coverage_omission_count": len(active_synthetic_omissions),
        "synthetic_coverage_omissions": active_synthetic_omissions,
        "invalidated_item_review_count": len(invalidated_items),
        "invalidated_coverage_omission_count": len(invalidated_omissions),
        "invalidated_item_review_shas": sorted(
            {record_content_sha(r) for r in invalidated_items}
        ),
        "observed_silent_drop_item_ids": silent_drop_item_ids,
        "item_review_log_count": len(scoped_items),
        "coverage_review_log_count": len(scoped_cov),
        # Back-compat aliases = human-only.
        "reviewed_item_count": len(reviewed_ids),
        "unreviewed_item_count": len(unreviewed),
        "unreviewed_item_ids": unreviewed,
        "dimension_counts": dim_counts,
        "coverage_omissions": active_human_omissions,
        "retained_with_failed_or_uncertain_support_predicate_or_value": problem_retained,
    }


def main_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record append-only extraction item or coverage judgments. "
            "Does not edit receipts or evidence hashes."
        )
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    item = sub.add_parser("record-item", help="Append an item-level review")
    item.add_argument("--run", required=True)
    item.add_argument("--artifact", required=True)
    item.add_argument("--chunk-sha", required=True)
    item.add_argument("--item-id", required=True)
    item.add_argument("--origin", required=True, choices=["human", "synthetic_test"])
    item.add_argument("--reviewer-id", required=True)
    item.add_argument("--reviewer-role", required=True)
    for dim in ITEM_DIMENSIONS:
        item.add_argument(
            f"--{dim.replace('_', '-')}",
            required=True,
            choices=["pass", "fail", "uncertain", "not_applicable"],
        )
    item.add_argument("--notes", default="")
    item.add_argument("--store", default=None)
    item.add_argument(
        "--refresh",
        action="store_true",
        help="Regenerate comparison pages + diagnostic summary after recording",
    )

    cov = sub.add_parser("record-omission", help="Append a chunk-coverage omission")
    cov.add_argument("--run", required=True)
    cov.add_argument("--artifact", required=True)
    cov.add_argument("--chunk-sha", required=True)
    cov.add_argument("--source-locator", required=True)
    cov.add_argument("--description", required=True)
    cov.add_argument("--origin", required=True, choices=["human", "synthetic_test"])
    cov.add_argument("--reviewer-id", required=True)
    cov.add_argument("--reviewer-role", required=True)
    cov.add_argument("--proposed-predicate", default=None)
    cov.add_argument(
        "--proposed-not-provisional",
        action="store_true",
        help="Mark proposed predicate as non-provisional (default is provisional)",
    )
    cov.add_argument("--span-start", type=int, default=None)
    cov.add_argument("--span-end", type=int, default=None)
    cov.add_argument("--notes", default="")
    cov.add_argument("--store", default=None)
    cov.add_argument("--refresh", action="store_true")

    inv = sub.add_parser(
        "invalidate-contaminated",
        help="Append invalidations for contaminated live diagnostic review rows",
    )
    inv.add_argument("--run", default=DIAGNOSTIC_RUN_ID)
    inv.add_argument("--store", default=None)
    inv.add_argument("--refresh", action="store_true")

    args = parser.parse_args(argv)
    store = ReceiptStore(Path(args.store) if args.store else None)

    if args.cmd == "record-item":
        judgments = {dim: getattr(args, dim) for dim in ITEM_DIMENSIONS}
        row = append_item_review(
            store,
            run_id=args.run,
            artifact_id=args.artifact,
            chunk_sha256=args.chunk_sha,
            item_id=args.item_id,
            origin=args.origin,
            reviewer_id=args.reviewer_id,
            reviewer_role=args.reviewer_role,
            judgments=judgments,
            notes=args.notes,
        )
        print(json.dumps(row.model_dump(mode="json"), indent=2))
        if args.refresh:
            from evals.history.refresh_extraction_review_surfaces import refresh_all

            refresh_all(store=store, run_id=args.run, artifact_id=args.artifact)
        return 0

    if args.cmd == "record-omission":
        row = append_coverage_omission(
            store,
            run_id=args.run,
            artifact_id=args.artifact,
            chunk_sha256=args.chunk_sha,
            source_locator=args.source_locator,
            description=args.description,
            origin=args.origin,
            reviewer_id=args.reviewer_id,
            reviewer_role=args.reviewer_role,
            proposed_predicate=args.proposed_predicate,
            proposed_predicate_provisional=not args.proposed_not_provisional,
            source_span_start=args.span_start,
            source_span_end=args.span_end,
            notes=args.notes,
        )
        print(json.dumps(row.model_dump(mode="json"), indent=2))
        if args.refresh:
            from evals.history.refresh_extraction_review_surfaces import refresh_all

            refresh_all(store=store, run_id=args.run, artifact_id=args.artifact)
        return 0

    if args.cmd == "invalidate-contaminated":
        counts = invalidate_contaminated_live_reviews(store, run_id=args.run)
        print(json.dumps(counts, indent=2))
        if args.refresh:
            from evals.history.refresh_extraction_review_surfaces import refresh_all

            refresh_all(store=store, run_id=args.run)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main_cli())
