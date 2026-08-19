"""Predicate promotion path — hatch marker, register, half-registration guard."""

from __future__ import annotations

from extract import draft_to_fact
from schemas import Child, ExtractedFactDraft, Source

_CHILD = Child(name="Taylor Nguyen", dob="2010-03-22", evaluation_date="2025-07-11")


def _source() -> Source:
    return Source(
        id="doc_x",
        type="school",
        date="2023-09-18",
        label="doc_x",
        content="Widget inventory this period is complete. Grade 11 roster on file.",
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


def test_proposed_draft_marks_fact_is_proposed() -> None:
    draft = _draft(
        predicate="__unregistered__",
        proposed_predicate="widget_inventory_status",
        value="complete",
        value_text="Widget inventory this period is complete.",
    )
    fact = draft_to_fact(draft, fact_id="f_doc_x_001", source=_source(), child=_CHILD)
    assert fact.is_proposed is True
    assert fact.predicate == "widget_inventory_status"


def test_registered_draft_is_not_proposed() -> None:
    fact = draft_to_fact(_draft(), fact_id="f_doc_x_001", source=_source(), child=_CHILD)
    assert fact.is_proposed is False
    assert fact.predicate == "grade"
