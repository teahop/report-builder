"""Prompt-render checks for the lean History extraction decision procedure."""

from __future__ import annotations

from pathlib import Path

from extract import build_extract_system_prompt

_PROMPT = Path(__file__).resolve().parent / "extract_prompt.md"


def test_extract_prompt_has_claim_decision_procedure() -> None:
    text = _PROMPT.read_text(encoding="utf-8")
    assert "## Claim → predicate → value" in text
    assert "Identify the supported claim and its domain" in text
    assert "`__unregistered__`" in text
    assert "### Compact examples" in text
    assert "written_expression" in text
    assert "math_computation" in text
    assert "math_fluency" in text
    assert "classroom_engagement" in text


def test_extract_prompt_dedupes_grade_iep_attendance_hard_rule() -> None:
    text = _PROMPT.read_text(encoding="utf-8")
    # Domain section remains; repeated hard-rule #8 must not.
    assert "## Grade, IEP status, attendance, medications" in text
    assert "Course titles" in text or "Math 10" in text
    assert "Do not invent `grade`, `iep_status`, or `attendance`" not in text


def test_rendered_system_prompt_includes_predicate_list_and_procedure() -> None:
    rendered = build_extract_system_prompt()
    assert "{{PREDICATE_LIST}}" not in rendered
    assert "## Claim → predicate → value" in rendered
    assert "written_expression" in rendered
    # Prefer faithful match over nearest registered label.
    assert "Match predicate to claim domain" in rendered
    assert "Prefer registered predicates; use `__unregistered__`" not in rendered
