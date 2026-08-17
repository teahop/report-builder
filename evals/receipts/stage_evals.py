"""Append-only stage eval records (eval-only; independent of receipts)."""

from __future__ import annotations

import json
from pathlib import Path

from evals.receipts.models import DecisionOrigin, StageEvalRecord
from evals.receipts.store import ReceiptStore, utc_now


def evals_path(store: ReceiptStore, run_id: str) -> Path:
    return store.run_dir(run_id) / "evals.jsonl"


def load_eval_records(store: ReceiptStore, run_id: str) -> list[StageEvalRecord]:
    path = evals_path(store, run_id)
    if not path.exists():
        return []
    out: list[StageEvalRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(StageEvalRecord.model_validate_json(line))
    return out


def load_eval_records_for_artifact(
    store: ReceiptStore, run_id: str, artifact_id: str
) -> list[StageEvalRecord]:
    return [
        e for e in load_eval_records(store, run_id) if e.artifact_id == artifact_id
    ]


def append_eval_record(
    store: ReceiptStore,
    *,
    run_id: str,
    artifact_id: str,
    check_id: str,
    check_version: str,
    result: str,
    evidence_item_ids: list[str] | None = None,
    detail: str | None = None,
    evaluator_id: str | None = None,
    evaluator_origin: DecisionOrigin | str | None = "system",
    recorded_at: str | None = None,
    expected_sha256: str | None = None,
) -> StageEvalRecord:
    """
    Append a stage eval without mutating the receipt or evidence view.

    Regenerates the current review page and run index.
    """

    receipt = store.load_receipt(run_id, artifact_id)
    sha = expected_sha256 or receipt.artifact_sha256
    if sha != receipt.artifact_sha256:
        raise ValueError(
            f"eval SHA {sha[:12]} does not match receipt artifact "
            f"{receipt.artifact_sha256[:12]}"
        )

    row = StageEvalRecord(
        artifact_id=artifact_id,
        artifact_sha256=sha,
        check_id=check_id,
        check_version=check_version,
        result=result,  # type: ignore[arg-type]
        evidence_item_ids=list(evidence_item_ids or []),
        detail=detail,
        recorded_at=recorded_at or utc_now(),
        evaluator_id=evaluator_id,
        evaluator_origin=evaluator_origin,  # type: ignore[arg-type]
    )
    path = evals_path(store, run_id)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(row.model_dump_json() + "\n")

    # Late import avoids circular import at module load.
    from evals.receipts.review import rebuild_current_review_view, rebuild_review_index

    rebuild_current_review_view(store, run_id, artifact_id)
    rebuild_review_index(store, run_id)
    return row


def main_cli(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Append a stage-eval record")
    parser.add_argument("--run", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--check-id", required=True)
    parser.add_argument("--check-version", required=True)
    parser.add_argument("--result", required=True, choices=["pass", "fail", "skip"])
    parser.add_argument("--detail", default=None)
    parser.add_argument("--evaluator-id", default=None)
    parser.add_argument(
        "--evaluator-origin", default="system", choices=["human", "synthetic_test", "system"]
    )
    parser.add_argument("--store", default=None)
    args = parser.parse_args(argv)
    store = ReceiptStore(Path(args.store) if args.store else None)
    row = append_eval_record(
        store,
        run_id=args.run,
        artifact_id=args.artifact,
        check_id=args.check_id,
        check_version=args.check_version,
        result=args.result,
        detail=args.detail,
        evaluator_id=args.evaluator_id,
        evaluator_origin=args.evaluator_origin,
    )
    print(json.dumps(row.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
