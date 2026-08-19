"""Declared per-predicate value shapes — type mismatches, not topic names."""

from __future__ import annotations

from extract import _draft_is_skippable
from normalize import value_fits_shape
from schemas import ExtractedFactDraft, Source


def _draft(**kwargs) -> ExtractedFactDraft:
    base = {
        "subject": "child",
        "predicate": "attendance",
        "value": "83",
        "value_text": "On task(OT) | 83%",
        "assertion": "asserted",
        "life_stage": "current",
        "confidence": "stated",
    }
    base.update(kwargs)
    return ExtractedFactDraft.model_validate(base)


def _source(content: str) -> Source:
    return Source(
        id="doc_x",
        type="observation",
        date="2023-09-18",
        label="doc_x",
        content=content,
        doc_class="narrative",
    )


def test_percent_is_not_an_attendance_count() -> None:
    assert not value_fits_shape("attendance", "83", "On task(OT) | 83%")
    assert not value_fits_shape("attendance", "17", "Off task on phone | 17%")
    source = _source("On task(OT) | 83%\nOff task on phone | 17%")
    assert _draft_is_skippable(_draft(), source)


def test_day_count_and_status_fit_attendance() -> None:
    assert value_fits_shape("attendance", "12", "12 absences")
    assert value_fits_shape("attendance", "regular", "attendance is regular")
    source = _source("Attendance this period: 12 absences.")
    draft = _draft(value="12", value_text="12 absences")
    assert not _draft_is_skippable(draft, source)


def test_discipline_narrative_does_not_fit_attendance() -> None:
    text = (
        "Student was found in possession of a vape. He is frequently out of class, "
        "roaming the campus, or in the bathroom."
    )
    assert not value_fits_shape(
        "attendance",
        "frequently out of class, roaming the campus, or in the bathroom",
        text,
    )


def test_name_field_fill_does_not_fit_organization() -> None:
    content = """
Name of individual being evaluated
Client ID
Date of report
Diego Fenton
School
Grade
"""
    assert not value_fits_shape(
        "school_enrollment", "diego fenton", "Diego Fenton", content
    )
    assert value_fits_shape(
        "school_enrollment",
        "Meadowbrook High School",
        "attends Meadowbrook High School",
        "Student currently attends Meadowbrook High School.",
    )
