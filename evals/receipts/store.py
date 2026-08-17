"""Content-addressed receipt store and run helpers (eval-only)."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from evals.receipts.hashing import (
    ContentAddressConflict,
    canonical_json_bytes,
    write_content_addressed,
    write_content_addressed_text,
)
from evals.receipts.models import (
    ArtifactRef,
    FileRef,
    LineageKind,
    RECEIPT_VERSION,
    StageConfig,
    StageReceipt,
)

_RECEIPTS_ROOT = Path(__file__).resolve().parent
_DEFAULT_STORE = _RECEIPTS_ROOT / "store"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id(prefix: str = "run") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"


def new_artifact_id(stage: str) -> str:
    return f"art_{stage}_{uuid4().hex[:12]}"


def try_git_sha(repo_hint: Path | None = None) -> str | None:
    if repo_hint is not None:
        root = repo_hint
    else:
        root = _RECEIPTS_ROOT
        for candidate in (_RECEIPTS_ROOT, *_RECEIPTS_ROOT.parents):
            if (candidate / ".git").exists():
                root = candidate
                break
        else:
            root = _RECEIPTS_ROOT.parents[1]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


class ReceiptStore:
    """
    Layout::

        store/
          by_sha/<sha>.json|.md
          runs/<run_id>/
            receipts/<artifact_id>.json
            decisions.jsonl
            evals.jsonl
            index.md                      # rebuildable
            review_views/current/<id>.md  # rebuildable current review
            evidence_views/<id>.md        # named pointer to immutable evidence
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or _DEFAULT_STORE
        self.by_sha = self.root / "by_sha"
        self.runs = self.root / "runs"
        self.by_sha.mkdir(parents=True, exist_ok=True)
        self.runs.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        path = self.runs / run_id
        path.mkdir(parents=True, exist_ok=True)
        (path / "receipts").mkdir(exist_ok=True)
        (path / "review_views" / "current").mkdir(parents=True, exist_ok=True)
        (path / "evidence_views").mkdir(exist_ok=True)
        return path

    def put_json_artifact(self, obj: Any) -> FileRef:
        digest, path = write_content_addressed(self.by_sha, obj, suffix=".json")
        return FileRef(
            sha256=digest,
            relative_path=str(path.relative_to(self.root)),
            label="machine_json",
        )

    def put_text_artifact(self, text: str, *, suffix: str = ".md") -> FileRef:
        digest, path = write_content_addressed_text(
            self.by_sha, text, suffix=suffix
        )
        return FileRef(
            sha256=digest,
            relative_path=str(path.relative_to(self.root)),
            label="machine_text",
        )

    def write_receipt(self, receipt: StageReceipt) -> Path:
        run = self.run_dir(receipt.run_id)
        path = run / "receipts" / f"{receipt.artifact_id}.json"
        payload = receipt.model_dump(mode="json")
        data = canonical_json_bytes(payload)
        if path.exists() and path.read_bytes() != data:
            raise ContentAddressConflict(
                f"receipt {receipt.artifact_id} already exists with different bytes"
            )
        path.write_bytes(data)
        return path

    def load_receipt(self, run_id: str, artifact_id: str) -> StageReceipt:
        path = self.run_dir(run_id) / "receipts" / f"{artifact_id}.json"
        return StageReceipt.model_validate_json(path.read_text(encoding="utf-8"))

    def list_receipts(self, run_id: str) -> list[StageReceipt]:
        receipt_dir = self.run_dir(run_id) / "receipts"
        out: list[StageReceipt] = []
        for path in sorted(receipt_dir.glob("*.json")):
            out.append(StageReceipt.model_validate_json(path.read_text(encoding="utf-8")))
        return out

    def read_artifact_json(self, ref: FileRef) -> Any:
        if not ref.relative_path:
            raise FileNotFoundError("FileRef.relative_path required")
        path = self.root / ref.relative_path
        return json.loads(path.read_text(encoding="utf-8"))

    def read_artifact_text(self, ref: FileRef) -> str:
        if not ref.relative_path:
            raise FileNotFoundError("FileRef.relative_path required")
        return (self.root / ref.relative_path).read_text(encoding="utf-8")


def build_receipt(
    *,
    store: ReceiptStore,
    run_id: str,
    stage: str,
    machine_payload: Any,
    config: StageConfig | None = None,
    parents: list[ArtifactRef] | None = None,
    inputs: list[ArtifactRef] | None = None,
    deterministic_decisions: Any | None = None,
    counts: dict[str, int] | None = None,
    tokens: dict[str, Any] | None = None,
    latency_ms: float | None = None,
    lineage: LineageKind = "evaluable",
    notes: str | None = None,
    external_trace: dict[str, Any] | None = None,
    artifact_id: str | None = None,
    created_at: str | None = None,
) -> StageReceipt:
    """
    Hash the primary machine payload, store an immutable evidence view, and
    emit a v2 receipt. Eval results and review status are **not** embedded.
    """

    from evals.receipts.render import render_evidence_markdown
    from evals.receipts.review import rebuild_current_review_view, rebuild_review_index

    machine_ref = store.put_json_artifact(machine_payload)
    decisions_ref = None
    decisions_payload = None
    if deterministic_decisions is not None:
        decisions_payload = deterministic_decisions
        decisions_ref = store.put_json_artifact(deterministic_decisions)

    aid = artifact_id or new_artifact_id(stage)
    cfg = config or StageConfig()
    if cfg.git_sha is None:
        cfg = cfg.model_copy(update={"git_sha": try_git_sha()})

    # Build a provisional receipt object for evidence rendering (no evidence_view yet).
    provisional = StageReceipt(
        receipt_version=RECEIPT_VERSION,
        run_id=run_id,
        stage=stage,
        artifact_id=aid,
        artifact_sha256=machine_ref.sha256,
        created_at=created_at or utc_now(),
        parents=list(parents or []),
        inputs=list(inputs or []),
        config=cfg,
        machine_output=machine_ref,
        deterministic_decisions=decisions_ref,
        evidence_view=None,
        review_view=None,
        external_trace=external_trace,
        counts=dict(counts or {}),
        tokens=tokens,
        latency_ms=latency_ms,
        eval_results=[],
        lineage=lineage,
        notes=notes,
    )
    evidence_md = render_evidence_markdown(
        provisional, decisions_payload=decisions_payload
    )
    # Guard: evidence view must not claim review status.
    lowered = evidence_md.lower()
    if "review status:" in lowered or "latest decision:" in lowered:
        raise RuntimeError("evidence view must not include review status")

    evidence_ref = store.put_text_artifact(evidence_md, suffix=".md")
    named_ev = store.run_dir(run_id) / "evidence_views" / f"{aid}.md"
    named_ev.write_text(evidence_md, encoding="utf-8")

    receipt = provisional.model_copy(update={"evidence_view": evidence_ref})
    store.write_receipt(receipt)

    rebuild_current_review_view(store, run_id, aid)
    rebuild_review_index(store, run_id)
    return receipt


__all__ = [
    "ReceiptStore",
    "build_receipt",
    "new_run_id",
    "new_artifact_id",
    "try_git_sha",
    "utc_now",
]
