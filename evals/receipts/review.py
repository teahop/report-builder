"""Append-only human review decisions and rebuildable current views (eval-only)."""

from __future__ import annotations

import json
from pathlib import Path

from evals.receipts.models import (
    FORBIDDEN_AUTO_HUMAN_IDS,
    DecisionOrigin,
    ReviewDecision,
    StageReceipt,
)
from evals.receipts.store import ReceiptStore, utc_now


class ReviewError(ValueError):
    """Invalid review transition or missing artifact."""


def decisions_path(store: ReceiptStore, run_id: str) -> Path:
    return store.run_dir(run_id) / "decisions.jsonl"


def load_decisions(store: ReceiptStore, run_id: str) -> list[ReviewDecision]:
    path = decisions_path(store, run_id)
    if not path.exists():
        return []
    out: list[ReviewDecision] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        # v1 decisions lacked origin — treat as unknown, do not invent human.
        if "origin" not in raw:
            raw["origin"] = "synthetic_test"
            raw.setdefault("reviewer_id", "receipt_test_harness")
            raw.setdefault("reviewer_role", "automated_test")
            # Preserve historical invalid ids for inspection; skip model validation
            # by constructing carefully for display-only load.
            try:
                out.append(ReviewDecision.model_validate(raw))
            except Exception:
                # Flawed contract-v1 rows (e.g. tj identity) stay readable.
                out.append(
                    ReviewDecision.model_construct(
                        decision_version=str(raw.get("decision_version", "1")),
                        artifact_id=raw["artifact_id"],
                        artifact_sha256=raw["artifact_sha256"],
                        decision=raw["decision"],
                        origin="synthetic_test",  # type: ignore[arg-type]
                        reviewer_id=raw.get("reviewer_id", "?"),
                        reviewer_role=raw.get("reviewer_role", "?"),
                        reviewed_at=raw["reviewed_at"],
                        notes=raw.get("notes", "")
                        + " [LOADED_INVALID_V1_IDENTITY]",
                        replacement_artifact_id=raw.get("replacement_artifact_id"),
                        replacement_sha256=raw.get("replacement_sha256"),
                    )
                )
            continue
        out.append(ReviewDecision.model_validate(raw))
    return out


def latest_decision_for(
    decisions: list[ReviewDecision], artifact_id: str
) -> ReviewDecision | None:
    latest: ReviewDecision | None = None
    for d in decisions:
        if d.artifact_id == artifact_id:
            latest = d
    return latest


def review_status(store: ReceiptStore, run_id: str, artifact_id: str) -> str:
    latest = latest_decision_for(load_decisions(store, run_id), artifact_id)
    if latest is None:
        return "unreviewed"
    return latest.decision


def is_accepted(
    store: ReceiptStore,
    run_id: str,
    artifact_id: str,
    *,
    expected_sha256: str | None = None,
    require_human: bool = False,
) -> bool:
    decisions = load_decisions(store, run_id)
    latest = latest_decision_for(decisions, artifact_id)
    if latest is None or latest.decision != "accepted":
        return False
    if require_human and latest.origin != "human":
        return False
    if expected_sha256 is not None and latest.artifact_sha256 != expected_sha256:
        return False
    receipt = store.load_receipt(run_id, artifact_id)
    if receipt.artifact_sha256 != latest.artifact_sha256:
        return False
    if expected_sha256 is not None and receipt.artifact_sha256 != expected_sha256:
        return False
    return True


def _validate_transition(
    prior: ReviewDecision | None,
    new: ReviewDecision,
    *,
    store: ReceiptStore,
    run_id: str,
) -> None:
    if prior is None:
        return
    if prior.decision == "accepted" and new.decision == "accepted":
        if prior.artifact_sha256 != new.artifact_sha256:
            raise ReviewError(
                "cannot re-accept the same artifact_id with a different SHA"
            )
        return
    if prior.decision == "rejected" and new.decision == "accepted":
        raise ReviewError(
            "rejected artifact cannot later be accepted; produce a new artifact_id"
        )
    if prior.decision == "superseded" and new.decision != "superseded":
        raise ReviewError("superseded artifact cannot change decision kind")
    if new.decision == "superseded":
        if not new.replacement_artifact_id or not new.replacement_sha256:
            raise ReviewError("superseded requires replacement")
        if not is_accepted(
            store,
            run_id,
            new.replacement_artifact_id,
            expected_sha256=new.replacement_sha256,
        ):
            raise ReviewError(
                "superseded replacement must already be an accepted artifact"
            )


def current_review_path(store: ReceiptStore, run_id: str, artifact_id: str) -> Path:
    return store.run_dir(run_id) / "review_views" / "current" / f"{artifact_id}.md"


def rebuild_current_review_view(
    store: ReceiptStore, run_id: str, artifact_id: str
) -> Path:
    from evals.receipts.render import render_current_review_markdown

    receipt = store.load_receipt(run_id, artifact_id)
    md = render_current_review_markdown(store, receipt)
    path = current_review_path(store, run_id, artifact_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return path


def record_decision(
    store: ReceiptStore,
    *,
    run_id: str,
    artifact_id: str,
    decision: str,
    origin: DecisionOrigin | str,
    reviewer_id: str,
    reviewer_role: str,
    notes: str = "",
    replacement_artifact_id: str | None = None,
    replacement_sha256: str | None = None,
    reviewed_at: str | None = None,
) -> ReviewDecision:
    if origin == "human" and reviewer_id.strip().lower() in FORBIDDEN_AUTO_HUMAN_IDS:
        # Allowed only when explicitly supplied after real review — still warn
        # via notes? Spec says human records an identifier after that person
        # actually reviews. Forbidden list is for automatic emission; CLI/human
        # may use tj after real review. Do not block human tj.
        pass
    if origin == "synthetic_test" and reviewer_id.strip().lower() in FORBIDDEN_AUTO_HUMAN_IDS:
        raise ReviewError(
            f"synthetic_test must not use human identity {reviewer_id!r}"
        )

    receipt = store.load_receipt(run_id, artifact_id)
    row = ReviewDecision(
        artifact_id=artifact_id,
        artifact_sha256=receipt.artifact_sha256,
        decision=decision,  # type: ignore[arg-type]
        origin=origin,  # type: ignore[arg-type]
        reviewer_id=reviewer_id,
        reviewer_role=reviewer_role,
        reviewed_at=reviewed_at or utc_now(),
        notes=notes,
        replacement_artifact_id=replacement_artifact_id,
        replacement_sha256=replacement_sha256,
    )
    prior = latest_decision_for(load_decisions(store, run_id), artifact_id)
    _validate_transition(prior, row, store=store, run_id=run_id)

    path = decisions_path(store, run_id)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(row.model_dump_json() + "\n")

    rebuild_current_review_view(store, run_id, artifact_id)
    rebuild_review_index(store, run_id)
    return row


def require_accepted_parent(
    store: ReceiptStore,
    *,
    run_id: str,
    artifact_id: str,
    expected_sha256: str,
) -> None:
    """Fail if a parent is not accepted at the exact SHA (any truthful origin)."""

    if not is_accepted(
        store, run_id, artifact_id, expected_sha256=expected_sha256
    ):
        status = review_status(store, run_id, artifact_id)
        raise ReviewError(
            f"parent {artifact_id} is {status}; evaluable children require accepted "
            f"at sha={expected_sha256[:12]}"
        )


def rebuild_review_index(
    store: ReceiptStore,
    run_id: str,
    *,
    banner: str | None = None,
) -> Path:
    """Rebuildable human index — not a receipt / not a source of truth."""

    receipts = store.list_receipts(run_id)
    decisions = load_decisions(store, run_id)
    lines = [
        f"# Review index — `{run_id}`",
        "",
    ]
    if banner:
        lines += [f"> {banner}", ""]
    lines += [
        "_Rebuildable index. Receipts, decisions.jsonl, and evals.jsonl are "
        "the sources of truth. Per-artifact current views live under "
        "`review_views/current/`._",
        "",
        "| Artifact | Stage | Lineage | SHA-256 (12) | Status | Origin | Reviewer |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in receipts:
        latest = latest_decision_for(decisions, r.artifact_id)
        status = latest.decision if latest else "unreviewed"
        reviewer = latest.reviewer_id if latest else "—"
        origin = getattr(latest, "origin", None) if latest else "—"
        lines.append(
            f"| `{r.artifact_id}` | `{r.stage}` | `{r.lineage}` | "
            f"`{r.artifact_sha256[:12]}` | **{status}** | `{origin}` | {reviewer} |"
        )
    lines.append("")
    lines.append("## Current review pages")
    lines.append("")
    for r in receipts:
        rel = f"review_views/current/{r.artifact_id}.md"
        lines.append(f"- [`{r.artifact_id}`]({rel})")
    lines.append("")
    lines.append("## Decision log (append-only)")
    lines.append("")
    if not decisions:
        lines.append("_No decisions yet — all artifacts unreviewed._")
    else:
        for d in decisions:
            origin = getattr(d, "origin", "unknown")
            lines.append(
                f"- `{d.reviewed_at}` · `{d.artifact_id}` · **{d.decision}** · "
                f"origin=`{origin}` · {d.reviewer_id}/{d.reviewer_role}"
                + (f" — {d.notes}" if d.notes else "")
            )
    path = store.run_dir(run_id) / "index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def mark_run_index_invalid(store: ReceiptStore, run_id: str, banner: str) -> Path:
    """Rewrite rebuildable index with a clear invalid-demo banner; leave receipts."""

    # Ensure current views exist for inspection, then banner the index.
    for r in store.list_receipts(run_id):
        try:
            rebuild_current_review_view(store, run_id, r.artifact_id)
        except Exception:
            pass
    return rebuild_review_index(store, run_id, banner=banner)


def main_cli(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Record a stage-receipt review decision")
    sub = parser.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="Append a review decision")
    rec.add_argument("--run", required=True)
    rec.add_argument("--artifact", required=True)
    rec.add_argument(
        "--decision", required=True, choices=["accepted", "rejected", "superseded"]
    )
    rec.add_argument(
        "--origin", required=True, choices=["human", "synthetic_test"]
    )
    rec.add_argument("--reviewer-id", required=True)
    rec.add_argument("--reviewer-role", required=True)
    rec.add_argument("--notes", default="")
    rec.add_argument("--replacement-artifact", default=None)
    rec.add_argument("--replacement-sha", default=None)
    rec.add_argument("--store", default=None)

    idx = sub.add_parser("index", help="Rebuild the review index for a run")
    idx.add_argument("--run", required=True)
    idx.add_argument("--store", default=None)

    args = parser.parse_args(argv)
    store = ReceiptStore(Path(args.store) if args.store else None)
    if args.cmd == "record":
        row = record_decision(
            store,
            run_id=args.run,
            artifact_id=args.artifact,
            decision=args.decision,
            origin=args.origin,
            reviewer_id=args.reviewer_id,
            reviewer_role=args.reviewer_role,
            notes=args.notes,
            replacement_artifact_id=args.replacement_artifact,
            replacement_sha256=args.replacement_sha,
        )
        print(json.dumps(row.model_dump(mode="json"), indent=2))
        return 0
    if args.cmd == "index":
        path = rebuild_review_index(store, args.run)
        print(path)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main_cli())
