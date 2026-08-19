"""Predicate promotion path — hatch marker, register, half-registration guard."""

from __future__ import annotations

from typing import Any

from extract import accumulate_predicate_proposals, build_ledger, draft_to_fact
from provider import ModelProvider, StructuredResult
from schemas import (
    Child,
    ExtractedFactDraft,
    PredicateProposal,
    Source,
    SourceExtraction,
)

_CHILD = Child(name="Taylor Nguyen", dob="2010-03-22", evaluation_date="2025-07-11")


def _source(*, source_id: str = "doc_x") -> Source:
    return Source(
        id=source_id,
        type="school",
        date="2023-09-18",
        label=source_id,
        content=(
            "School notes\n"
            "The teacher recorded that widget inventory is complete for this period. "
            "Student is listed in grade 11 on the roster."
        ),
        doc_class="narrative",
    )


def _draft(**kwargs) -> ExtractedFactDraft:
    base = {
        "subject": "child",
        "predicate": "grade",
        "value": "11",
        "value_text": "Student is listed in grade 11 on the roster.",
        "assertion": "asserted",
        "life_stage": "school-age",
        "confidence": "stated",
    }
    base.update(kwargs)
    return ExtractedFactDraft.model_validate(base)


def _proposed_draft() -> ExtractedFactDraft:
    return _draft(
        predicate="__unregistered__",
        proposed_predicate="widget_inventory_status",
        value="inventory recorded as complete for this period",
        value_text="The teacher recorded that widget inventory is complete for this period.",
    )


class _FixedExtractProvider(ModelProvider):
    def __init__(self, extraction: SourceExtraction) -> None:
        self._client = None  # type: ignore[assignment]
        self.extraction = extraction
        self.calls = 0

    def complete_structured(self, **kwargs: Any) -> StructuredResult:  # type: ignore[override]
        self.calls += 1
        return StructuredResult(
            data=self.extraction,
            total_tokens=10,
            prompt_tokens=8,
            completion_tokens=2,
        )


def test_proposed_draft_marks_fact_is_proposed() -> None:
    draft = _proposed_draft()
    fact = draft_to_fact(draft, fact_id="f_doc_x_001", source=_source(), child=_CHILD)
    assert fact.is_proposed is True
    assert fact.predicate == "widget_inventory_status"


def test_registered_draft_is_not_proposed() -> None:
    fact = draft_to_fact(_draft(), fact_id="f_doc_x_001", source=_source(), child=_CHILD)
    assert fact.is_proposed is False
    assert fact.predicate == "grade"


def test_two_runs_proposing_the_same_name_accumulate_count() -> None:
    provider = _FixedExtractProvider(SourceExtraction(facts=[_proposed_draft()]))
    ledger1, *_rest = build_ledger(
        provider, child=_CHILD, sources=[_source(source_id="doc_a")], model="gpt-4o-mini"
    )
    ledger2, _, _, _, review, *_ = build_ledger(
        provider,
        child=_CHILD,
        sources=[_source(source_id="doc_b")],
        model="gpt-4o-mini",
        prior_ledger=ledger1,
    )
    assert [p.name for p in ledger2.predicate_proposals] == ["widget_inventory_status"]
    assert ledger2.predicate_proposals[0].count == 2
    assert review == ["widget_inventory_status"]


def test_run_proposing_nothing_leaves_register_unchanged() -> None:
    hatch = _FixedExtractProvider(SourceExtraction(facts=[_proposed_draft()]))
    prior, *_ = build_ledger(
        hatch, child=_CHILD, sources=[_source(source_id="doc_a")], model="gpt-4o-mini"
    )
    snapshot = [p.model_copy() for p in prior.predicate_proposals]
    registered = _FixedExtractProvider(SourceExtraction(facts=[_draft()]))
    later, *_ = build_ledger(
        registered,
        child=_CHILD,
        sources=[_source(source_id="doc_b")],
        model="gpt-4o-mini",
        prior_ledger=prior,
    )
    assert later.predicate_proposals == snapshot
    assert later.predicate_proposals[0].count == 1


def test_accumulate_helper_dedupes_by_name() -> None:
    first = draft_to_fact(
        _proposed_draft(), fact_id="f_a_001", source=_source(source_id="doc_a"), child=_CHILD
    )
    second = draft_to_fact(
        _proposed_draft(), fact_id="f_b_001", source=_source(source_id="doc_b"), child=_CHILD
    )
    once = accumulate_predicate_proposals([], [first])
    twice = accumulate_predicate_proposals(once, [second])
    empty = accumulate_predicate_proposals(twice, [])
    assert once == [
        PredicateProposal(
            name="widget_inventory_status",
            count=1,
            first_seen_at="2023-09-18",
            last_seen_at="2023-09-18",
            example_source_id="doc_a",
        )
    ]
    assert twice[0].count == 2
    assert twice[0].example_source_id == "doc_a"
    assert empty == twice
