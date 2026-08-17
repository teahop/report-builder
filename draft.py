"""Section drafting from a settled ledger + must-mention conflicts."""

from __future__ import annotations

import json
from pathlib import Path

from conflicts import compute_timelines
from draft_output import (
    finalize_draft_output,
    output_to_report_section,
    render_annotated_review,
)
from schemas import (
    Conflict,
    Disagreement,
    DraftProseOutput,
    DraftRequest,
    DraftResponse,
    Fact,
    Ledger,
    ReportSection,
    ReviewItem,
    ReviewQueue,
    SectionName,
    SourcedFact,
    Timeline,
)
from validators import compute_age_years

_DIR = Path(__file__).resolve().parent

# Re-export so existing `from draft import finalize_draft_output` callers keep working.
_output_to_report_section = output_to_report_section


def section_has_supporting_facts(ledger: Ledger, section: SectionName) -> bool:
    """
    Conditional sections: no supporting facts → do not draft a thin section.

    For history, any non-empty ledger is sufficient. Future sections may filter
    by predicate/life_stage.
    """

    if section == "history":
        return len(ledger.facts) > 0
    return len(ledger.facts) > 0


def _fact_dict(f: Fact) -> dict:
    return {
        "fact_id": f.id,
        "subject": f.subject,
        "predicate": f.predicate,
        "qualifier": f.qualifier,
        "value": f.value,
        "value_text": f.value_text,
        "assertion": f.assertion,
        "source_id": f.source_id,
        "source_date": f.source_date,
        "as_of_date": f.as_of_date,
        "reporter": f.reporter,
        "life_stage": f.life_stage,
        "grade": f.grade,
        "temporality": f.temporality,
        "confidence": f.confidence,
        "derivation": f.derivation,
        "inherits_dispute": f.inherits_dispute,
    }


def _timeline_payload(timelines: list[Timeline]) -> list[dict]:
    return [
        {
            "subject": t.subject,
            "predicate": t.predicate,
            "qualifier": t.qualifier,
            "topic": t.topic,
            "entries": [
                {
                    "fact_id": e.fact_id,
                    "value": e.value,
                    "value_text": e.value_text,
                    "as_of_date": e.as_of_date,
                    "source_id": e.source_id,
                    "source_date": e.source_date,
                    "assertion": e.assertion,
                    "is_latest": e.is_latest,
                }
                for e in t.entries
            ],
        }
        for t in timelines
    ]


def _disagreement_payload(items: list[Disagreement]) -> list[dict]:
    return [
        {
            "topic": d.topic,
            "subject": d.subject,
            "predicate": d.predicate,
            "qualifier": d.qualifier,
            "predicate_class": d.predicate_class,
            "versions": [
                {
                    "fact_id": v.fact_id,
                    "source_id": v.source_id,
                    "source_date": v.source_date,
                    "reporter": v.reporter,
                    "value": v.value,
                    "value_text": v.value_text,
                    "assertion": v.assertion,
                }
                for v in d.versions
            ],
        }
        for d in items
    ]


def _draft_user_payload(body: DraftRequest, *, timeline_shaped: bool = True) -> str:
    """
    Build the drafter user packet.

    timeline_shaped=True (default): durable facts flat; as_of facts as ordered timelines.
    timeline_shaped=False: flat facts list (Stage 4.6 shape) — for A/B chronology check.
    """

    source_labels = {s.id: {"label": s.label, "date": s.date} for s in body.ledger.sources}
    packet: dict = {
        "section": body.section,
        "child": body.ledger.child.model_dump(),
        "stale_as_of_days": body.stale_as_of_days,
        "source_labels": source_labels,
        "must_mention_conflicts": _disagreement_payload(body.conflicts),
        "variance": _disagreement_payload(body.variance),
    }
    if timeline_shaped:
        durable = [_fact_dict(f) for f in body.ledger.facts if f.temporality == "durable"]
        timelines = compute_timelines(body.ledger.facts)
        packet["durable_facts"] = durable
        packet["timelines"] = _timeline_payload(timelines)
        packet["note"] = (
            "durable_facts are atemporal. timelines are as_of progressions "
            "ordered by as_of_date — use them for chronological narrative. "
            "Cite fact_id from either list. "
            "When stating current age, cite the derived age_years entry "
            "(source_id=computed, derivation='dob + evaluation_date')."
        )
    else:
        packet["facts"] = [_fact_dict(f) for f in body.ledger.facts]
    return json.dumps(packet, indent=2)


def history_package_to_draft_response(hist, body: DraftRequest) -> DraftResponse:
    """Flatten a HistoryDraftResponse into the course DraftResponse contract."""

    model = body.model or hist.model or "gpt-4o-mini"
    if not hist.section_populated:
        return DraftResponse(
            section_populated=False,
            empty_reason=hist.empty_reason or "No History sections had supporting blocks",
            answer=None,
            review=hist.review,
            unverified_citations=[],
            failed_citation_attempts=[],
            annotated_prose=None,
            unanchored_quotes=[],
            tokens_used=hist.tokens_used,
            tokens_by_stage=hist.tokens_by_stage,
            model=model,
            latency_ms=hist.latency_ms,
            cost_usd=hist.cost_usd,
            age_years_expected=compute_age_years(
                body.ledger.child.dob, body.ledger.child.evaluation_date
            ),
        )

    blocks = []
    statements = []
    prose_parts: list[str] = []
    for drafted in hist.package.sections:
        if drafted.draft_output:
            if drafted.draft_output.blocks:
                blocks.extend(drafted.draft_output.blocks)
            else:
                statements.extend(drafted.draft_output.statements)
                if drafted.draft_output.prose.strip():
                    prose_parts.append(drafted.draft_output.prose.strip())
        elif drafted.legacy_draft and drafted.legacy_draft.answer:
            prose_parts.append(drafted.legacy_draft.answer.prose)
    if blocks:
        combined = finalize_draft_output(
            DraftProseOutput(blocks=blocks, prose="", statements=[]),
            body.ledger,
        )
    else:
        combined = DraftProseOutput(
            blocks=[],
            prose="\n\n".join(prose_parts),
            statements=statements,
        )
    section = output_to_report_section(
        combined,
        section=body.section,
        ledger=body.ledger,
        conflicts=body.conflicts,
    )
    if not section.facts:
        # Fallback: union of per-section legacy answers (prose-only stub path).
        merged_facts = []
        for drafted in hist.package.sections:
            if drafted.legacy_draft and drafted.legacy_draft.answer:
                merged_facts.extend(drafted.legacy_draft.answer.facts)
                if not combined.prose and drafted.legacy_draft.answer.prose:
                    combined = combined.model_copy(
                        update={"prose": drafted.legacy_draft.answer.prose}
                    )
        if merged_facts:
            section = section.model_copy(
                update={
                    "facts": merged_facts,
                    "prose": combined.prose or section.prose,
                }
            )
    annotated_prose, unanchored_quotes = render_annotated_review(combined)
    unverified = []
    failed = []
    for drafted in hist.package.sections:
        if drafted.legacy_draft is None:
            continue
        unverified.extend(drafted.legacy_draft.unverified_citations)
        failed.extend(drafted.legacy_draft.failed_citation_attempts)
    expected_age = None
    for drafted in hist.package.sections:
        if drafted.legacy_draft is not None and drafted.legacy_draft.age_years_expected is not None:
            expected_age = drafted.legacy_draft.age_years_expected
            break
    if expected_age is None:
        expected_age = compute_age_years(
            body.ledger.child.dob, body.ledger.child.evaluation_date
        )
    return DraftResponse(
        section_populated=True,
        empty_reason=None,
        answer=section,
        review=hist.review,
        unverified_citations=unverified,
        failed_citation_attempts=failed,
        annotated_prose=annotated_prose,
        unanchored_quotes=unanchored_quotes,
        tokens_used=hist.tokens_used,
        tokens_by_stage=hist.tokens_by_stage,
        model=model,
        latency_ms=hist.latency_ms,
        cost_usd=hist.cost_usd,
        age_years_expected=expected_age,
    )


def draft_section(
    provider,
    body: DraftRequest,
    *,
    timeline_shaped: bool = True,
) -> DraftResponse:
    """Course /ask adapter — production drafting is POST /draft/history.

    `timeline_shaped` is ignored: the History case brief always carries timelines.
    """

    del timeline_shaped
    if not section_has_supporting_facts(body.ledger, body.section):
        review = ReviewQueue(
            items=[
                ReviewItem(
                    kind="section_empty",
                    summary=(
                        f"Section {body.section!r} cannot be populated — "
                        "no supporting facts in the ledger. This is a legitimate "
                        "outcome when sources for this section were not collected."
                    ),
                    requires_decision=False,
                )
            ]
        )
        return DraftResponse(
            section_populated=False,
            empty_reason=f"No ledger facts for section {body.section!r}",
            answer=None,
            review=review,
            unverified_citations=[],
            failed_citation_attempts=[],
            annotated_prose=None,
            unanchored_quotes=[],
            tokens_used=0,
            tokens_by_stage={"draft": 0, "entailment": 0},
            model=body.model or "gpt-4o-mini",
            latency_ms=0,
            cost_usd=0.0,
            age_years_expected=compute_age_years(
                body.ledger.child.dob, body.ledger.child.evaluation_date
            ),
        )

    from history_draft import draft_history_package
    from history_schemas import HistoryDraftRequest

    hist = draft_history_package(
        provider,
        HistoryDraftRequest(
            confirm_synthetic=True,
            ledger=body.ledger,
            conflicts=body.conflicts,
            variance=body.variance,
            model=body.model,
            entailment_model=body.entailment_model,
            stale_as_of_days=body.stale_as_of_days,
            skip_entailment=False,
        ),
    )
    return history_package_to_draft_response(hist, body)
