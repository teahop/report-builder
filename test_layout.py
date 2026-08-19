"""Document-structure occupancy — banner fragments and partial name-column rows."""

from __future__ import annotations

from pathlib import Path

from extract import _draft_is_skippable
from layout import is_document_structure_value
from schemas import ExtractedFactDraft, Source


def _draft(**kwargs) -> ExtractedFactDraft:
    base = {
        "subject": "child",
        "predicate": "school_enrollment",
        "value": "fenton",
        "value_text": "Fenton 8th Grade Social Studies Late Start",
        "assertion": "asserted",
        "life_stage": "current",
        "confidence": "stated",
    }
    base.update(kwargs)
    return ExtractedFactDraft.model_validate(base)


def _source(content: str) -> Source:
    return Source(
        id="doc_x",
        type="school",
        date="2023-09-18",
        label="doc_x",
        content=content,
        doc_class="narrative",
    )


_BANNER = """
[ANONYMIZED TEXT RENDITION]
Fenton 8th Grade Social Studies Late Start
Complete 96.72%
Overall Grade 88.0%
Start Date: 4/4/2021
"""

_IDENTITY_ROW = """
Print Student Attendance
StuID     Last Name                    First Name             Middle Name                        Gender     Grade
552016    Fenton                     Diego                  Andres Rafael                    Male       11
        2023-2024                                           Meadowbrook High School
"""

_NARRATIVE_SCHOOL = """
Student currently attends Meadowbrook High School in grade 11.
Enrollment began August 2023.
"""


def test_banner_last_name_fragment_is_structure() -> None:
    source = _source(_BANNER)
    draft = _draft(value="fenton", value_text="Fenton 8th Grade Social Studies Late Start")
    assert is_document_structure_value(draft, source)
    assert _draft_is_skippable(draft, source)


def test_middle_plus_last_from_identity_row_is_structure() -> None:
    source = _source(_IDENTITY_ROW)
    draft = _draft(
        predicate="legal_name",
        value="Andres Rafael Fenton",
        value_text="Andres Rafael Fenton",
    )
    assert is_document_structure_value(draft, source)
    assert _draft_is_skippable(draft, source)


def test_last_name_cell_alone_is_structure() -> None:
    source = _source(_IDENTITY_ROW)
    draft = _draft(value="fenton", value_text="Fenton")
    assert is_document_structure_value(draft, source)


def test_complete_first_last_from_identity_row_is_a_claim() -> None:
    source = _source(_IDENTITY_ROW)
    draft = _draft(
        predicate="legal_name",
        value="Diego Fenton",
        value_text="Diego Fenton",
    )
    assert not is_document_structure_value(draft, source)
    assert not _draft_is_skippable(draft, source)


def test_labeled_school_name_is_a_claim() -> None:
    source = _source(_NARRATIVE_SCHOOL)
    draft = _draft(value="Meadowbrook High School", value_text="attends Meadowbrook High School")
    assert not is_document_structure_value(draft, source)
    assert not _draft_is_skippable(draft, source)


def test_guard_does_not_name_a_predicate() -> None:
    text = (Path(__file__).resolve().parent / "layout.py").read_text(encoding="utf-8")
    assert "school_enrollment" not in text
    assert "legal_name" not in text
