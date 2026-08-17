"""Stage-receipt schemas, dispositions, and review decisions (eval-only).

Receipt version 2: eval results and mutable review status live outside the
immutable receipt (append-only ``evals.jsonl`` / ``decisions.jsonl``).
Version-1 receipts remain readable; do not mutate them in place.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

RECEIPT_VERSION = "2"
RECEIPT_VERSIONS_SUPPORTED = frozenset({"1", "2"})
REVIEW_DECISION_VERSION = "2"
STAGE_EVAL_RECORD_VERSION = "1"

# Deprecated embedding on v1 receipts — kept for read compatibility only.
EVAL_RESULT_VERSION = "1"

StageName = Literal[
    "extract_raw",
    "extract_transform",
    "ledger",
    "brief",
    "draft",
    "alignment",
    "assembly",
    "diagnostic_replay",
]

# Raw extraction → finalized fact: exactly one terminal disposition per raw item.
# ``observed_silent_drop`` is diagnostic-only (see validate.py).
ExtractDispositionKind = Literal[
    "retained",
    "transformed",
    "suppressed_duplicate",
    "quarantined",
    "not_draftable",
    "error",
    "observed_silent_drop",
]

# Ledger → brief: every fact accounted for (multi-destination reuse allowed).
BriefDispositionKind = Literal[
    "selected",
    "routed_elsewhere",
    "held_for_review",
    "suppressed_duplicate",
    "not_draftable",
]

ReviewDecisionKind = Literal["accepted", "rejected", "superseded"]
DecisionOrigin = Literal["human", "synthetic_test"]

LineageKind = Literal[
    "evaluable",
    "diagnostic_replay",
    "legacy_untraceable",
    "non_evaluable_preview",
]

FORBIDDEN_AUTO_HUMAN_IDS = frozenset(
    {"tj", "molly", "tj-tho", "teahop", "clinician"}
)
SYNTHETIC_REVIEWER_ID = "receipt_test_harness"
SYNTHETIC_REVIEWER_ROLE = "automated_test"


class ArtifactRef(BaseModel):
    stage: StageName | str | None = None
    artifact_id: str | None = None
    sha256: str
    name: str | None = None
    role: str | None = None
    required_accepted: bool = False


class FileRef(BaseModel):
    """Reference to a content-addressed or relative machine artifact."""

    sha256: str
    relative_path: str | None = None
    label: str | None = None


class StageConfig(BaseModel):
    git_sha: str | None = None
    code_fingerprint: str | None = None
    prompt_sha256: str | None = None
    structure_spec_id: str | None = None
    structure_spec_sha256: str | None = None
    schema_version: str | None = None
    model: str | None = None
    temperature: float | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    """Deprecated v1 embedded eval — prefer StageEvalRecord / evals.jsonl."""

    eval_result_version: str = EVAL_RESULT_VERSION
    check_id: str
    check_version: str
    artifact_id: str
    artifact_sha256: str
    result: Literal["pass", "fail", "skip"]
    evidence_item_ids: list[str] = Field(default_factory=list)
    detail: str | None = None


class StageEvalRecord(BaseModel):
    """Append-only stage eval — independent of the immutable receipt."""

    eval_record_version: str = STAGE_EVAL_RECORD_VERSION
    artifact_id: str
    artifact_sha256: str
    check_id: str
    check_version: str
    result: Literal["pass", "fail", "skip"]
    evidence_item_ids: list[str] = Field(default_factory=list)
    detail: str | None = None
    recorded_at: str
    evaluator_id: str | None = None
    evaluator_origin: DecisionOrigin | Literal["system"] | None = None


class ExtractDisposition(BaseModel):
    item_id: str
    kind: ExtractDispositionKind
    fact_id: str | None = None
    canonical_fact_id: str | None = None
    review_item_id: str | None = None
    reason: str | None = None
    gate_or_check: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    error: str | None = None

    @model_validator(mode="after")
    def _require_targets(self) -> ExtractDisposition:
        if self.kind in {"retained", "transformed"} and not self.fact_id:
            raise ValueError(f"{self.kind} requires fact_id")
        if self.kind == "transformed" and (self.before is None or self.after is None):
            raise ValueError("transformed requires before/after")
        if self.kind == "suppressed_duplicate" and not self.canonical_fact_id:
            raise ValueError("suppressed_duplicate requires canonical_fact_id")
        if self.kind == "quarantined" and (
            not self.review_item_id or not self.reason
        ):
            raise ValueError("quarantined requires review_item_id and reason")
        if self.kind == "not_draftable" and not self.reason:
            raise ValueError("not_draftable requires reason")
        if self.kind == "error" and not self.error:
            raise ValueError("error requires error details")
        if self.kind == "observed_silent_drop":
            if self.review_item_id:
                raise ValueError(
                    "observed_silent_drop must not mint a quarantine/review-item id"
                )
            if not self.reason or not self.gate_or_check:
                raise ValueError(
                    "observed_silent_drop requires gate_or_check and reason"
                )
        return self


class BriefDisposition(BaseModel):
    fact_id: str
    kind: BriefDispositionKind
    destinations: list[str] = Field(default_factory=list)
    routed_to: str | None = None
    canonical_fact_id: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _require_targets(self) -> BriefDisposition:
        if self.kind == "selected" and not self.destinations:
            raise ValueError("selected requires one or more destinations")
        if self.kind == "routed_elsewhere" and not self.routed_to:
            raise ValueError("routed_elsewhere requires routed_to")
        if self.kind == "suppressed_duplicate" and not self.canonical_fact_id:
            raise ValueError("suppressed_duplicate requires canonical_fact_id")
        if self.kind in {"held_for_review", "not_draftable"} and not self.reason:
            raise ValueError(f"{self.kind} requires reason")
        return self


class QuarantineReviewItem(BaseModel):
    review_item_id: str
    item_id: str
    reason: str
    detail: dict[str, Any] = Field(default_factory=dict)


class StageReceipt(BaseModel):
    """Immutable stage receipt envelope — records what happened; never mutates."""

    receipt_version: str = RECEIPT_VERSION
    run_id: str
    stage: StageName | str
    artifact_id: str
    artifact_sha256: str
    created_at: str  # metadata only — not part of primary artifact content hash
    parents: list[ArtifactRef] = Field(default_factory=list)
    inputs: list[ArtifactRef] = Field(default_factory=list)
    config: StageConfig = Field(default_factory=StageConfig)
    machine_output: FileRef
    deterministic_decisions: FileRef | None = None
    evidence_view: FileRef | None = None  # immutable, content-hashed
    review_view: FileRef | None = None  # v1 compat; v2 uses rebuildable current view
    external_trace: dict[str, Any] | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    tokens: dict[str, Any] | None = None
    latency_ms: float | None = None
    # v1 only — ignored for new writes; prefer evals.jsonl
    eval_results: list[EvalResult] = Field(default_factory=list)
    lineage: LineageKind = "evaluable"
    notes: str | None = None

    @model_validator(mode="after")
    def _supported_version(self) -> StageReceipt:
        if self.receipt_version not in RECEIPT_VERSIONS_SUPPORTED:
            raise ValueError(f"unsupported receipt_version {self.receipt_version}")
        return self


class ReviewDecision(BaseModel):
    decision_version: str = REVIEW_DECISION_VERSION
    artifact_id: str
    artifact_sha256: str
    decision: ReviewDecisionKind
    origin: DecisionOrigin
    reviewer_id: str
    reviewer_role: str
    reviewed_at: str
    notes: str = ""
    replacement_artifact_id: str | None = None
    replacement_sha256: str | None = None

    @model_validator(mode="after")
    def _validate_identity_and_replacement(self) -> ReviewDecision:
        if self.decision == "superseded":
            if not self.replacement_artifact_id or not self.replacement_sha256:
                raise ValueError(
                    "superseded requires replacement_artifact_id and replacement_sha256"
                )
        rid = self.reviewer_id.strip().lower()
        if self.origin == "synthetic_test":
            if rid in FORBIDDEN_AUTO_HUMAN_IDS:
                raise ValueError(
                    f"synthetic_test must not use human identity {self.reviewer_id!r}"
                )
            if rid != SYNTHETIC_REVIEWER_ID:
                raise ValueError(
                    f"synthetic_test reviewer_id must be {SYNTHETIC_REVIEWER_ID!r}"
                )
            if self.reviewer_role != SYNTHETIC_REVIEWER_ROLE:
                raise ValueError(
                    f"synthetic_test reviewer_role must be {SYNTHETIC_REVIEWER_ROLE!r}"
                )
        if self.origin == "human" and rid == SYNTHETIC_REVIEWER_ID:
            raise ValueError("human origin cannot use receipt_test_harness identity")
        return self
