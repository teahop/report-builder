"""Reason for Referral — typed case context, request/response, and draft output.

Separate from history `SectionName` / `DraftBlock` / life-stage coverage.
Field names and confirmation states follow:
`docs/product/Reason for Referral — input, drafting, and validation contract.md`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from schemas import Ledger, ReviewQueue

CaptureMethod = Literal[
    "document_extracted",
    "client_reported",
    "clinician_entered",
    "clinician_confirmed",
]

ConfirmationState = Literal[
    "confirmed",
    "unknown",
    "not_yet_collected",
    "not_applicable",
    "not_found_in_reviewed_sources",
    "conflicting",
]

EvaluationTypeValue = Literal[
    "private_psychoeducational_evaluation",
    "iee",
    "initial_special_education_evaluation",
    "reevaluation",
    "other",
]

SuspectedDisabilityCategory = Literal[
    "specific_learning_disability",
    "other_health_impairment",
    "autism",
    "emotional_disturbance",
    "speech_or_language_impairment",
    "intellectual_disability",
    "orthopedic_impairment",
    "traumatic_brain_injury",
    "visual_impairment",
    "deafness",
    "hard_of_hearing",
    "deaf_blindness",
    "multiple_disabilities",
    "established_medical_disability",
    "other",
]

SupportPlanType = Literal["none", "504", "iep", "other"]

ClientGoalPresentationMode = Literal["paraphrase", "verbatim_quote"]

DRAFTABLE_STATES: frozenset[ConfirmationState] = frozenset({"confirmed"})
EXPLICIT_UNAVAILABLE_STATES: frozenset[ConfirmationState] = frozenset(
    {
        "unknown",
        "not_applicable",
        "not_found_in_reviewed_sources",
    }
)
RESOLVED_STATES: frozenset[ConfirmationState] = DRAFTABLE_STATES | EXPLICIT_UNAVAILABLE_STATES


class ProvenanceMixin(BaseModel):
    """Shared provenance for every ReferralContext value."""

    context_id: str = Field(description="Stable id cited by draft statements")
    raw_text: str | None = Field(
        default=None,
        description="Source wording when available; preserved as evidence",
    )
    normalized_value: str | None = Field(
        default=None,
        description="Controlled or cleaned value for selection/validation/drafting",
    )
    source_id: str | None = None
    source_type: str | None = None
    source_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    as_of_date: str | None = Field(
        default=None,
        description="ISO date when different from source_date",
    )
    capture_method: CaptureMethod
    confirmation_state: ConfirmationState
    confirmed_by: str | None = None
    confirmed_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when clinician confirmed",
    )
    reviewed_source_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Sources reviewed when confirmation_state is "
            "not_found_in_reviewed_sources"
        ),
    )


class EvaluationTypeField(ProvenanceMixin):
    """Controlled evaluation type with provenance."""

    normalized_value: EvaluationTypeValue | None = None


class RequesterEntry(ProvenanceMixin):
    """One requester name + relationship/role."""

    name: str
    role: str | None = None


class ReferralTriggerField(ProvenanceMixin):
    """Short supported statement of why the evaluation was initiated."""


class PresentingConcern(ProvenanceMixin):
    """One ordered presenting-concern statement."""


class ClientGoal(ProvenanceMixin):
    """Client goal — raw wording is evidence; presentation defaults to paraphrase."""

    raw_text: str = Field(description="Client's own words when available; evidence only")
    presentation_mode: ClientGoalPresentationMode = Field(
        default="paraphrase",
        description=(
            "paraphrase by default; verbatim_quote only by explicit clinician selection"
        ),
    )


class PriorEvaluationField(ProvenanceMixin):
    """Earlier assessment for IEE / reevaluation context."""

    organization: str | None = None
    report_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    evaluation_type: str | None = None
    outcome: str | None = None


class AreaOfDisagreement(ProvenanceMixin):
    """One neutrally stated disagreement for an IEE trigger."""


class SuspectedDisability(ProvenanceMixin):
    """One confirmed or candidate suspected-disability category."""

    category: SuspectedDisabilityCategory
    other_label: str | None = Field(
        default=None,
        description="Required label when category is 'other'",
    )

    @model_validator(mode="after")
    def _other_label_required(self) -> SuspectedDisability:
        if self.category == "other" and not (self.other_label or "").strip():
            raise ValueError("other_label is required when category is 'other'")
        return self


class ExistingDiagnosis(ProvenanceMixin):
    """Referral-relevant diagnosis only — not a complete diagnosis inventory."""

    diagnosis: str
    diagnosing_provider: str | None = None
    date_or_status: str | None = None


class CurrentSupportContext(ProvenanceMixin):
    """Concise current-support mention when insufficiency is part of the referral."""

    plan_type: SupportPlanType
    insufficiency_concern: str | None = None


class NotesForDrafter(ProvenanceMixin):
    """Exceptional clinician-confirmed instruction — not a free-form second prompt."""


class ReferralContext(BaseModel):
    """Normalized case-context record for Reason for Referral drafting."""

    evaluation_type: EvaluationTypeField | None = None
    requested_by: list[RequesterEntry] = Field(default_factory=list)
    referral_trigger: ReferralTriggerField | None = None
    presenting_concerns: list[PresentingConcern] = Field(default_factory=list)
    client_goals: list[ClientGoal] = Field(default_factory=list)
    prior_evaluation: PriorEvaluationField | None = None
    areas_of_disagreement: list[AreaOfDisagreement] = Field(default_factory=list)
    suspected_disabilities: list[SuspectedDisability] = Field(default_factory=list)
    relevant_existing_diagnoses: list[ExistingDiagnosis] = Field(default_factory=list)
    current_support_context: CurrentSupportContext | None = None
    notes_for_drafter: NotesForDrafter | None = None


class ContextFieldItem(BaseModel):
    """Typed missing / candidate / conflicting surface item."""

    field: str
    confirmation_state: ConfirmationState
    reason: str
    context_ids: list[str] = Field(default_factory=list)
    candidate_values: list[str] = Field(default_factory=list)
    reviewed_source_ids: list[str] = Field(default_factory=list)
    requires_clinician_selection: bool = False


class ReferralDraftStatement(BaseModel):
    """One prose span traced to ReferralContext context_ids."""

    quote: str = Field(description="Exact span from its paragraph or category sentence")
    statement: str = Field(description="Supported claim")
    support_ids: list[str] = Field(
        min_length=1,
        description="ReferralContext context_id values supporting this claim",
    )


class ReferralParagraph(BaseModel):
    text: str
    statements: list[ReferralDraftStatement] = Field(min_length=1)


class ReferralDraftOutput(BaseModel):
    """Section-specific model output — categories last via server render."""

    paragraphs: list[ReferralParagraph] = Field(min_length=1, max_length=2)
    suspected_disabilities_sentence: str | None = Field(
        default=None,
        description=(
            "Optional traced sentence naming confirmed suspected categories. "
            "Server appends this to the end of the final paragraph."
        ),
    )
    suspected_disabilities_statements: list[ReferralDraftStatement] = Field(
        default_factory=list,
        description="Statements that cover the suspected-disabilities sentence",
    )


class ReferralDraftRequest(BaseModel):
    """Dedicated referral draft request — not an extension of DraftRequest."""

    confirm_synthetic: Literal[True] = Field(
        description=(
            "Must be true. Refuses real PHI/PII cases; OpenAI runtime is synthetic-only."
        ),
    )
    ledger: Ledger
    context: ReferralContext
    model: str | None = None
    eval_fixture_id: str | None = Field(
        default=None,
        description="Eval bookkeeping only — never reaches a model prompt.",
    )
    eval_run_index: int | None = Field(
        default=None,
        description="Eval bookkeeping only — never reaches a model prompt.",
    )


class ReferralDraftResponse(BaseModel):
    """Draft or typed context-completion result."""

    ready_for_draft: bool
    section_populated: bool
    missing_fields: list[ContextFieldItem] = Field(default_factory=list)
    candidate_fields: list[ContextFieldItem] = Field(default_factory=list)
    conflicting_fields: list[ContextFieldItem] = Field(default_factory=list)
    prose: str | None = None
    paragraphs: list[str] = Field(default_factory=list)
    statements: list[ReferralDraftStatement] = Field(default_factory=list)
    review: ReviewQueue = Field(default_factory=ReviewQueue)
    tokens_used: int = 0
    tokens_by_stage: dict[str, int] = Field(default_factory=dict)
    model: str
    latency_ms: int = 0
    cost_usd: float = 0.0
    prompt_sha256: str | None = None
    trace_id: str | None = None
    langfuse_url: str | None = None
