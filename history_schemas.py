"""History package schemas — generic section/block wrappers over DraftProseOutput.

Structural identity (keys, labels, order) is server-owned from the compiled plan.
No structure-specific Literal enums; swapping structure_spec_id must not require
new schema classes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from schemas import (
    DraftBlock,
    DraftProseOutput,
    DraftResponse,
    Disagreement,
    Ledger,
    ReviewQueue,
)

HistoryBlockKind = Literal["prose", "table"]
SectionPurpose = Literal["topic_history", "rater_input", "summary", "assessment"]


class DraftedBlock(BaseModel):
    """One assembled History block — identity from the plan, payload from drafting."""

    block_key: str
    display_label: str
    kind: HistoryBlockKind
    draft_block: DraftBlock
    fact_ids: list[str] = Field(default_factory=list)


class DraftedSection(BaseModel):
    section_key: str
    display_label: str
    purpose: str
    blocks: list[DraftedBlock] = Field(default_factory=list)
    draft_output: DraftProseOutput | None = None
    section_populated: bool = False
    empty_reason: str | None = None
    # Per-section DraftResponse fields preserved for review/cost consumers.
    legacy_draft: DraftResponse | None = None


class FactReuseRecord(BaseModel):
    fact_id: str
    section_key: str
    block_key: str
    purpose: str


class HistoryDraftPackage(BaseModel):
    structure_spec_id: str
    structure_spec_hash: str
    policy_hash: str
    voice_store_sha: str = ""
    sections: list[DraftedSection] = Field(default_factory=list)
    reuse_records: list[FactReuseRecord] = Field(default_factory=list)
    input_schema_gaps: list[str] = Field(default_factory=list)


class HistoryDraftRequest(BaseModel):
    """Isolated History-package request for POST /draft/history."""

    confirm_synthetic: Literal[True] = Field(
        description="Must be true. Synthetic/anonymized OpenAI path only.",
    )
    ledger: Ledger
    conflicts: list[Disagreement] = Field(default_factory=list)
    variance: list[Disagreement] = Field(default_factory=list)
    structure_spec_id: str = "provisional_tj_v1"
    model: str | None = None
    entailment_model: str | None = "gpt-4o-mini"
    stale_as_of_days: int = Field(default=365, ge=0)
    skip_entailment: bool = Field(
        default=False,
        description="Smoke/debug: skip per-statement entailment to reduce cost.",
    )


class HistoryPlanRequest(BaseModel):
    """Compile inspectable History briefs — no model call."""

    confirm_synthetic: Literal[True] = Field(
        description="Must be true. Synthetic/anonymized OpenAI path only.",
    )
    ledger: Ledger
    conflicts: list[Disagreement] = Field(default_factory=list)
    variance: list[Disagreement] = Field(default_factory=list)
    structure_spec_id: str = "provisional_tj_v1"


class HistorySectionBrief(BaseModel):
    section_key: str
    display_label: str
    purpose: str
    populated: bool
    blocks: list[str] = Field(default_factory=list)
    fact_count: int = 0
    markdown: str = ""


class HistoryPlanResponse(BaseModel):
    structure_spec_id: str
    sections: list[HistorySectionBrief] = Field(default_factory=list)
    input_schema_gaps: list[str] = Field(default_factory=list)


class HistoryDraftResponse(BaseModel):
    package: HistoryDraftPackage
    section_populated: bool
    empty_reason: str | None = None
    rendered_prose: str = ""
    review: ReviewQueue = Field(default_factory=ReviewQueue)
    tokens_used: int = 0
    tokens_by_stage: dict[str, int] = Field(default_factory=dict)
    model: str = ""
    latency_ms: int = 0
    cost_usd: float = 0.0
    trace_id: str | None = None
    langfuse_url: str | None = None
    prompt_hash: str = ""
    structure_spec_hash: str = ""
    voice_store_sha: str = ""
    voice_gate: dict | None = None
