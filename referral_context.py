"""Deterministic ReferralContext preflight — no model calls.

Surfaces missing, candidate, conflicting, and explicit-unavailable states
before any drafting spend. Ledger `referral_reason` facts become unconfirmed
candidates only.
"""

from __future__ import annotations

from dataclasses import dataclass

from referral_schemas import (
    DRAFTABLE_STATES,
    EXPLICIT_UNAVAILABLE_STATES,
    RESOLVED_STATES,
    ClientGoal,
    ContextFieldItem,
    EvaluationTypeValue,
    ProvenanceMixin,
    ReferralContext,
)
from schemas import Fact, Ledger, ReviewItem, ReviewQueue

_LOAD_BEARING_ALWAYS = ("evaluation_type", "referral_trigger", "requested_by")
_IEE_CONDITIONAL = ("prior_evaluation", "areas_of_disagreement")


@dataclass(frozen=True, slots=True)
class ReferralPreflight:
    ready_for_draft: bool
    missing_fields: list[ContextFieldItem]
    candidate_fields: list[ContextFieldItem]
    conflicting_fields: list[ContextFieldItem]
    selected_context: ReferralContext
    review: ReviewQueue
    evaluation_type: EvaluationTypeValue | None


def _state_of(item: ProvenanceMixin | None) -> str | None:
    if item is None:
        return None
    return item.confirmation_state


def _is_confirmed(item: ProvenanceMixin | None) -> bool:
    return item is not None and item.confirmation_state in DRAFTABLE_STATES


def _is_explicit_unavailable(item: ProvenanceMixin | None) -> bool:
    return item is not None and item.confirmation_state in EXPLICIT_UNAVAILABLE_STATES


def _is_conflicting(item: ProvenanceMixin | None) -> bool:
    return item is not None and item.confirmation_state == "conflicting"


def _is_resolved(item: ProvenanceMixin | None) -> bool:
    return item is not None and item.confirmation_state in RESOLVED_STATES


def _confirmed_entries(items: list) -> list:
    return [i for i in items if i.confirmation_state in DRAFTABLE_STATES]


def _conflicting_entries(items: list) -> list:
    return [i for i in items if i.confirmation_state == "conflicting"]


def _display_value(item: ProvenanceMixin) -> str:
    if getattr(item, "name", None):
        role = getattr(item, "role", None)
        return f"{item.name}" + (f" ({role})" if role else "")
    if getattr(item, "category", None):
        other = getattr(item, "other_label", None)
        return other or str(item.category)
    if getattr(item, "diagnosis", None):
        return str(item.diagnosis)
    if getattr(item, "plan_type", None):
        return str(item.plan_type)
    if item.normalized_value:
        return str(item.normalized_value)
    if item.raw_text:
        return item.raw_text
    return item.context_id


def _iter_context_items(context: ReferralContext) -> list[tuple[str, ProvenanceMixin]]:
    out: list[tuple[str, ProvenanceMixin]] = []
    if context.evaluation_type is not None:
        out.append(("evaluation_type", context.evaluation_type))
    for item in context.requested_by:
        out.append(("requested_by", item))
    if context.referral_trigger is not None:
        out.append(("referral_trigger", context.referral_trigger))
    for item in context.presenting_concerns:
        out.append(("presenting_concerns", item))
    for item in context.client_goals:
        out.append(("client_goals", item))
    if context.prior_evaluation is not None:
        out.append(("prior_evaluation", context.prior_evaluation))
    for item in context.areas_of_disagreement:
        out.append(("areas_of_disagreement", item))
    for item in context.suspected_disabilities:
        out.append(("suspected_disabilities", item))
    for item in context.relevant_existing_diagnoses:
        out.append(("relevant_existing_diagnoses", item))
    if context.current_support_context is not None:
        out.append(("current_support_context", context.current_support_context))
    if context.notes_for_drafter is not None:
        out.append(("notes_for_drafter", context.notes_for_drafter))
    return out


def collect_selected_context(context: ReferralContext) -> ReferralContext:
    """Keep confirmed values only for the model payload / validators."""

    return ReferralContext(
        evaluation_type=(
            context.evaluation_type
            if _is_confirmed(context.evaluation_type)
            else None
        ),
        requested_by=_confirmed_entries(context.requested_by),
        referral_trigger=(
            context.referral_trigger
            if _is_confirmed(context.referral_trigger)
            else None
        ),
        presenting_concerns=_confirmed_entries(context.presenting_concerns),
        client_goals=_confirmed_entries(context.client_goals),
        prior_evaluation=(
            context.prior_evaluation
            if _is_confirmed(context.prior_evaluation)
            else None
        ),
        areas_of_disagreement=_confirmed_entries(context.areas_of_disagreement),
        suspected_disabilities=_confirmed_entries(context.suspected_disabilities),
        relevant_existing_diagnoses=_confirmed_entries(
            context.relevant_existing_diagnoses
        ),
        current_support_context=(
            context.current_support_context
            if _is_confirmed(context.current_support_context)
            else None
        ),
        notes_for_drafter=(
            context.notes_for_drafter
            if _is_confirmed(context.notes_for_drafter)
            else None
        ),
    )


def selected_context_index(context: ReferralContext) -> dict[str, ProvenanceMixin]:
    return {item.context_id: item for _, item in _iter_context_items(context)}


def _missing_item(field: str, reason: str) -> ContextFieldItem:
    return ContextFieldItem(
        field=field,
        confirmation_state="not_yet_collected",
        reason=reason,
        requires_clinician_selection=True,
    )


def _conflicting_item(
    field: str,
    items: list[ProvenanceMixin],
    reason: str,
) -> ContextFieldItem:
    return ContextFieldItem(
        field=field,
        confirmation_state="conflicting",
        reason=reason,
        context_ids=[i.context_id for i in items],
        candidate_values=[_display_value(i) for i in items],
        requires_clinician_selection=True,
    )


def ledger_referral_reason_candidates(ledger: Ledger) -> list[ContextFieldItem]:
    """Convert noisy ledger referral_reason facts into unconfirmed candidates only."""

    facts = [f for f in ledger.facts if f.predicate == "referral_reason"]
    if not facts:
        return []

    by_value: dict[str, list[Fact]] = {}
    for fact in facts:
        key = (fact.value or fact.value_text or fact.id).strip().lower()
        by_value.setdefault(key, []).append(fact)

    items: list[ContextFieldItem] = []
    for group in by_value.values():
        values = sorted(
            {
                (f.value_text or f.value or "").strip()
                for f in group
                if (f.value_text or f.value or "").strip()
            }
        )
        items.append(
            ContextFieldItem(
                field="referral_trigger",
                confirmation_state="not_yet_collected",
                reason=(
                    "Ledger referral_reason fact(s) are unconfirmed candidates only. "
                    "They must not become the referral trigger without clinician "
                    "confirmation — the predicate is noisy in both held-back fixtures."
                ),
                context_ids=[f.id for f in group],
                candidate_values=values,
                reviewed_source_ids=sorted({f.source_id for f in group}),
                requires_clinician_selection=True,
            )
        )
    return items


def prepare_referral_context(
    ledger: Ledger,
    context: ReferralContext,
) -> ReferralPreflight:
    """Validate cardinality/controlled values and decide ready_for_draft."""

    missing: list[ContextFieldItem] = []
    conflicting: list[ContextFieldItem] = []
    candidates = ledger_referral_reason_candidates(ledger)
    review_items: list[ReviewItem] = []

    # --- evaluation_type ---
    et = context.evaluation_type
    if et is None:
        missing.append(
            _missing_item(
                "evaluation_type",
                "Required evaluation type was not supplied.",
            )
        )
    elif _is_conflicting(et):
        conflicting.append(
            _conflicting_item(
                "evaluation_type",
                [et],
                "Evaluation type is conflicting; clinician must select one value.",
            )
        )
    elif et.confirmation_state == "not_yet_collected":
        missing.append(
            ContextFieldItem(
                field="evaluation_type",
                confirmation_state="not_yet_collected",
                reason="Evaluation type is marked not_yet_collected.",
                context_ids=[et.context_id],
                requires_clinician_selection=True,
            )
        )
    elif _is_explicit_unavailable(et):
        # Required field cannot be drafted without a confirmed type.
        missing.append(
            ContextFieldItem(
                field="evaluation_type",
                confirmation_state=et.confirmation_state,
                reason=(
                    "Evaluation type is explicitly unavailable "
                    f"({et.confirmation_state}); a confirmed type is required."
                ),
                context_ids=[et.context_id],
                reviewed_source_ids=list(et.reviewed_source_ids),
                requires_clinician_selection=True,
            )
        )
    elif _is_confirmed(et) and not et.normalized_value:
        missing.append(
            ContextFieldItem(
                field="evaluation_type",
                confirmation_state="not_yet_collected",
                reason="Confirmed evaluation_type is missing normalized_value.",
                context_ids=[et.context_id],
                requires_clinician_selection=True,
            )
        )

    evaluation_type_value: EvaluationTypeValue | None = (
        et.normalized_value if _is_confirmed(et) and et and et.normalized_value else None
    )

    # --- referral_trigger ---
    trigger = context.referral_trigger
    if trigger is None:
        missing.append(
            _missing_item(
                "referral_trigger",
                "Required referral trigger was not supplied.",
            )
        )
    elif _is_conflicting(trigger):
        conflicting.append(
            _conflicting_item(
                "referral_trigger",
                [trigger],
                "Referral trigger is conflicting; clinician must select one value.",
            )
        )
    elif trigger.confirmation_state == "not_yet_collected":
        missing.append(
            ContextFieldItem(
                field="referral_trigger",
                confirmation_state="not_yet_collected",
                reason="Referral trigger is marked not_yet_collected.",
                context_ids=[trigger.context_id],
                requires_clinician_selection=True,
            )
        )
    elif _is_explicit_unavailable(trigger):
        missing.append(
            ContextFieldItem(
                field="referral_trigger",
                confirmation_state=trigger.confirmation_state,
                reason=(
                    "Referral trigger is explicitly unavailable "
                    f"({trigger.confirmation_state}); a confirmed trigger is required."
                ),
                context_ids=[trigger.context_id],
                reviewed_source_ids=list(trigger.reviewed_source_ids),
                requires_clinician_selection=True,
            )
        )
    elif _is_confirmed(trigger) and not (
        (trigger.normalized_value or trigger.raw_text or "").strip()
    ):
        missing.append(
            ContextFieldItem(
                field="referral_trigger",
                confirmation_state="not_yet_collected",
                reason="Confirmed referral_trigger has empty raw/normalized text.",
                context_ids=[trigger.context_id],
                requires_clinician_selection=True,
            )
        )

    # --- requested_by (required when known; omitted → collect) ---
    req_conflict = _conflicting_entries(context.requested_by)
    req_confirmed = _confirmed_entries(context.requested_by)
    if req_conflict:
        conflicting.append(
            _conflicting_item(
                "requested_by",
                req_conflict,
                "Requester values conflict; clinician must select who requested.",
            )
        )
    elif not req_confirmed:
        # Preserve explicit unavailable on a single sentinel entry if present.
        unavailable = [
            r
            for r in context.requested_by
            if r.confirmation_state in EXPLICIT_UNAVAILABLE_STATES
        ]
        if unavailable:
            # Known-unknown: do not treat as missing.
            pass
        elif any(r.confirmation_state == "not_yet_collected" for r in context.requested_by):
            pending = [
                r for r in context.requested_by if r.confirmation_state == "not_yet_collected"
            ]
            missing.append(
                ContextFieldItem(
                    field="requested_by",
                    confirmation_state="not_yet_collected",
                    reason="Requester is marked not_yet_collected.",
                    context_ids=[r.context_id for r in pending],
                    requires_clinician_selection=True,
                )
            )
        else:
            missing.append(
                _missing_item(
                    "requested_by",
                    "Requester was not supplied; confirm who initiated the evaluation "
                    "or mark explicitly unknown / not found.",
                )
            )

    # --- IEE conditional fields ---
    if evaluation_type_value == "iee":
        prior = context.prior_evaluation
        if prior is None:
            missing.append(
                _missing_item(
                    "prior_evaluation",
                    "IEE requires prior-evaluation context or an explicit unavailable state.",
                )
            )
        elif _is_conflicting(prior):
            conflicting.append(
                _conflicting_item(
                    "prior_evaluation",
                    [prior],
                    "Prior evaluation is conflicting; clinician must select one.",
                )
            )
        elif prior.confirmation_state == "not_yet_collected":
            missing.append(
                ContextFieldItem(
                    field="prior_evaluation",
                    confirmation_state="not_yet_collected",
                    reason="IEE prior evaluation is marked not_yet_collected.",
                    context_ids=[prior.context_id],
                    requires_clinician_selection=True,
                )
            )
        elif not _is_resolved(prior):
            missing.append(
                ContextFieldItem(
                    field="prior_evaluation",
                    confirmation_state=prior.confirmation_state,
                    reason="IEE prior evaluation is unresolved.",
                    context_ids=[prior.context_id],
                    requires_clinician_selection=True,
                )
            )

        disagree_conflict = _conflicting_entries(context.areas_of_disagreement)
        disagree_confirmed = _confirmed_entries(context.areas_of_disagreement)
        disagree_unavailable = [
            a
            for a in context.areas_of_disagreement
            if a.confirmation_state in EXPLICIT_UNAVAILABLE_STATES
        ]
        if disagree_conflict:
            conflicting.append(
                _conflicting_item(
                    "areas_of_disagreement",
                    disagree_conflict,
                    "IEE disagreement statements conflict; clinician must select.",
                )
            )
        elif not disagree_confirmed and not disagree_unavailable:
            if any(
                a.confirmation_state == "not_yet_collected"
                for a in context.areas_of_disagreement
            ):
                pending = [
                    a
                    for a in context.areas_of_disagreement
                    if a.confirmation_state == "not_yet_collected"
                ]
                missing.append(
                    ContextFieldItem(
                        field="areas_of_disagreement",
                        confirmation_state="not_yet_collected",
                        reason="IEE disagreement is marked not_yet_collected.",
                        context_ids=[a.context_id for a in pending],
                        requires_clinician_selection=True,
                    )
                )
            elif not context.areas_of_disagreement:
                missing.append(
                    _missing_item(
                        "areas_of_disagreement",
                        "IEE requires areas of disagreement or an explicit unavailable state.",
                    )
                )

    # --- suspected disabilities: conflicting blocks; unconfirmed stay candidates ---
    sus_conflict = _conflicting_entries(context.suspected_disabilities)
    if sus_conflict:
        conflicting.append(
            _conflicting_item(
                "suspected_disabilities",
                sus_conflict,
                "Suspected disability categories conflict; clinician must select scope.",
            )
        )
    for item in context.suspected_disabilities:
        if item.confirmation_state == "not_yet_collected":
            candidates.append(
                ContextFieldItem(
                    field="suspected_disabilities",
                    confirmation_state="not_yet_collected",
                    reason=(
                        "Suspected disability category requires confirmation for "
                        "current evaluation scope."
                    ),
                    context_ids=[item.context_id],
                    candidate_values=[_display_value(item)],
                    requires_clinician_selection=True,
                )
            )

    # Preserve explicit unavailable states as distinct from omitted/missing.
    for field, item in _iter_context_items(context):
        if item.confirmation_state in EXPLICIT_UNAVAILABLE_STATES:
            # Already handled for required fields above; still surface in review.
            review_items.append(
                ReviewItem(
                    kind="section_empty",
                    summary=(
                        f"{field} is explicitly {item.confirmation_state}"
                        + (
                            f" (reviewed: {', '.join(item.reviewed_source_ids)})"
                            if item.reviewed_source_ids
                            else ""
                        )
                    ),
                    requires_decision=False,
                )
            )

    for item in missing + conflicting:
        review_items.append(
            ReviewItem(
                kind="section_empty",
                summary=f"{item.field}: {item.reason}",
                requires_decision=item.requires_clinician_selection,
            )
        )

    ready = not missing and not conflicting
    selected = collect_selected_context(context) if ready else ReferralContext()

    return ReferralPreflight(
        ready_for_draft=ready,
        missing_fields=missing,
        candidate_fields=candidates,
        conflicting_fields=conflicting,
        selected_context=selected,
        review=ReviewQueue(items=review_items),
        evaluation_type=evaluation_type_value,
    )


def build_referral_model_payload(
    *,
    student_display_name: str,
    selected_context: ReferralContext,
    evaluation_type: EvaluationTypeValue | None,
) -> dict:
    """Case-specific user payload — display name + selected context only.

    Deliberately excludes DOB, evaluation date, age, grade, school, and placement.
    """

    def dump_item(item: ProvenanceMixin) -> dict:
        data = item.model_dump()
        # Strip empty optional noise for the prompt.
        return {k: v for k, v in data.items() if v not in (None, [], "")}

    def dump_goal(goal: ClientGoal) -> dict:
        data = dump_item(goal)
        mode = goal.presentation_mode
        data["presentation_mode"] = mode
        if mode == "verbatim_quote":
            data["quote_ready"] = True
            data["client_language_use"] = "verbatim_quote_authorized"
        else:
            data["quote_ready"] = False
            data["client_language_use"] = "evidence_for_paraphrase_only"
            # Prefer normalized_value for drafting when present.
            if goal.normalized_value:
                data["preferred_drafting_value"] = goal.normalized_value
        return data

    payload: dict = {
        "student_display_name": student_display_name,
        "evaluation_branch": evaluation_type,
        "selected_context": {
            "evaluation_type": (
                dump_item(selected_context.evaluation_type)
                if selected_context.evaluation_type
                else None
            ),
            "requested_by": [dump_item(i) for i in selected_context.requested_by],
            "referral_trigger": (
                dump_item(selected_context.referral_trigger)
                if selected_context.referral_trigger
                else None
            ),
            "presenting_concerns": [
                dump_item(i) for i in selected_context.presenting_concerns
            ],
            "client_goals": [dump_goal(i) for i in selected_context.client_goals],
            "prior_evaluation": (
                dump_item(selected_context.prior_evaluation)
                if selected_context.prior_evaluation
                else None
            ),
            "areas_of_disagreement": [
                dump_item(i) for i in selected_context.areas_of_disagreement
            ],
            "suspected_disabilities": [
                dump_item(i) for i in selected_context.suspected_disabilities
            ],
            "relevant_existing_diagnoses": [
                dump_item(i) for i in selected_context.relevant_existing_diagnoses
            ],
            "current_support_context": (
                dump_item(selected_context.current_support_context)
                if selected_context.current_support_context
                else None
            ),
            "notes_for_drafter": (
                dump_item(selected_context.notes_for_drafter)
                if selected_context.notes_for_drafter
                else None
            ),
        },
    }
    return payload


# Silence unused-name lint for documented constant groups.
_ = (_LOAD_BEARING_ALWAYS, _IEE_CONDITIONAL, _state_of)
