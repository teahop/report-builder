"""Regression tests for History evidence gates — source snippets, not hand-edited cache."""

from __future__ import annotations

import json
from pathlib import Path

from extract import _draft_is_skippable
from history_compiler import compile_history_plan, render_evidence_brief_markdown
from history_evidence import (
    is_academic_as_developmental_history,
    is_behavioral_support_as_health_plan,
    is_transient_fatigue_as_sleep,
)
from history_selectors import (
    select_birth_developmental_history,
    select_health_history,
    select_previous_evaluations,
)
from schemas import Child, ExtractedFactDraft, Fact, Ledger, Source

_DIR = Path(__file__).resolve().parent
_FIXTURE = _DIR / "fixtures" / "fixture_001"


def _load_doc_content(doc_id: str) -> str:
    data = json.loads((_FIXTURE / f"{doc_id}.json").read_text(encoding="utf-8"))
    if "sources" in data:
        return data["sources"][0]["content"]
    return data.get("content") or ""


def _draft(**kwargs) -> ExtractedFactDraft:
    base = {
        "subject": "child",
        "predicate": "sleep",
        "value": "tired",
        "value_text": "I'm tired. But fine.",
        "assertion": "asserted",
        "life_stage": "current",
        "confidence": "stated",
        "temporality": "as_of",
    }
    base.update(kwargs)
    return ExtractedFactDraft.model_validate(base)


def _source(doc_id: str, content: str, **kwargs) -> Source:
    defaults = dict(
        id=doc_id,
        type="school",
        date="2024-10-02",
        label=doc_id,
        content=content,
        doc_class="narrative",
    )
    defaults.update(kwargs)
    return Source(**defaults)


def test_academic_weakness_not_developmental_history() -> None:
    content = _load_doc_content("doc_11")
    assert "academic weakness" in content.lower() or "academic" in content.lower()
    snippet = (
        "Emma Rose Callahan demonstrates academic weakness in the areas of "
        "math fluency/numerical operations and written language."
    )
    assert is_academic_as_developmental_history(
        "academic weakness in math fluency/numerical operations and written language",
        snippet,
    )
    draft = _draft(
        predicate="developmental_history",
        value="academic weakness in math fluency/numerical operations and written language",
        value_text=snippet,
    )
    assert _draft_is_skippable(draft, _source("doc_11", content))

    # Explicit developmental characterization must keep.
    keep = _draft(
        predicate="developmental_history",
        value="typical",
        value_text="Developmental milestones were typical.",
    )
    assert not _draft_is_skippable(keep, _source("doc_11", content))


def test_behavioral_support_not_health_plan() -> None:
    content = _load_doc_content("doc_13")
    assert "support system is essential" in content.lower()
    snippet = (
        "current support system is essential for maintaining Emma Rose Callahan's "
        "safety and preventing escalation of behavioral issues"
    )
    assert is_behavioral_support_as_health_plan("active", snippet)
    draft = _draft(
        predicate="health_plan_status",
        value="active",
        value_text=snippet,
    )
    assert _draft_is_skippable(
        draft, _source("doc_13", content, type="other", date="2025-12-15")
    )

    keep = _draft(
        predicate="health_plan_status",
        value="none",
        value_text="Student does not require an individual health plan at this time.",
    )
    assert not _draft_is_skippable(keep, _source("doc_13", content, type="other"))


def test_transient_fatigue_not_sleep_vs_explicit_sleep_report() -> None:
    content = _load_doc_content("doc_21")
    assert "tired" in content.lower()
    fatigue = _draft(
        predicate="sleep",
        value="tired",
        value_text="How do you feel today? Sleep, breakfast, etc. I'm tired. But fine.",
    )
    assert is_transient_fatigue_as_sleep(fatigue.value, fatigue.value_text)
    assert _draft_is_skippable(
        fatigue, _source("doc_21", content, type="observation", date="2025-04-19")
    )

    explicit = _draft(
        predicate="sleep",
        value="poor without medications",
        value_text="Mother described sleep as poor without medications but fine with them.",
    )
    assert not is_transient_fatigue_as_sleep(explicit.value, explicit.value_text)
    assert not _draft_is_skippable(
        explicit, _source("doc_21", content, type="observation", date="2025-04-19")
    )


def _fact(**kwargs) -> Fact:
    defaults = dict(
        subject="child",
        qualifier=None,
        assertion="asserted",
        as_of_date=None,
        reporter=None,
        life_stage="current",
        grade=None,
        temporality="durable",
        confidence="stated",
        derivation=None,
        inherits_dispute=False,
        valence="neutral",
        source_section=None,
    )
    defaults.update(kwargs)
    return Fact(**defaults)


def test_selectors_gate_smoke_failure_patterns() -> None:
    """Compiler/selectors refuse the known wrong extractions even if present in ledger."""

    sources = [
        Source(
            id="doc_11",
            type="school",
            date="2024-10-02",
            label="IEP",
            content=_load_doc_content("doc_11")[:2000],
            doc_class="narrative",
        ),
        Source(
            id="doc_13",
            type="other",
            date="2025-12-15",
            label="WRAP letter",
            content=_load_doc_content("doc_13"),
            doc_class="narrative",
        ),
        Source(
            id="doc_21",
            type="observation",
            date="2025-04-19",
            label="Student interview",
            content=_load_doc_content("doc_21"),
            doc_class="narrative",
        ),
        Source(
            id="doc_26",
            type="prior_eval",
            date="2013-09-10",
            label="Prior diagnostic assessment",
            content=_load_doc_content("doc_26")[:2000],
            doc_class="narrative",
        ),
    ]
    facts = [
        _fact(
            id="f_doc_11_006",
            predicate="developmental_history",
            value="academic weakness in math fluency/numerical operations and written language",
            value_text="academic weakness in math fluency/numerical operations and written language",
            source_id="doc_11",
            source_date="2024-10-02",
            as_of_date="2024-10-02",
        ),
        _fact(
            id="f_walk",
            predicate="walked_age_months",
            value="19",
            value_text="walked at about 19 months",
            source_id="doc_26",
            source_date="2013-09-10",
            as_of_date="2013-09-10",
            life_stage="infancy",
        ),
        _fact(
            id="f_doc_13_005",
            predicate="health_plan_status",
            value="active",
            value_text=(
                "current support system is essential for maintaining safety "
                "and preventing escalation of behavioral issues"
            ),
            source_id="doc_13",
            source_date="2025-12-15",
            as_of_date="2025-12-15",
            temporality="as_of",
        ),
        _fact(
            id="f_health_ok",
            predicate="health_plan_status",
            value="none",
            value_text="does not require a health plan at this time",
            source_id="doc_11",
            source_date="2024-10-02",
            as_of_date="2024-10-02",
            temporality="as_of",
        ),
        _fact(
            id="f_doc_21_003",
            predicate="sleep",
            value="tired",
            value_text="I'm tired. But fine.",
            source_id="doc_21",
            source_date="2025-04-19",
            as_of_date="2025-04-19",
            temporality="as_of",
        ),
        _fact(
            id="f_doc_26_001",
            predicate="dob",
            value="2010-03-22",
            value_text="DOB: 3/22/10",
            source_id="doc_26",
            source_date="2013-09-10",
            as_of_date="2013-09-10",
        ),
        _fact(
            id="f_doc_26_002",
            predicate="age_years",
            value="3",
            value_text="Age: 3y 1m 23d",
            source_id="doc_26",
            source_date="2013-09-10",
            as_of_date="2013-09-10",
        ),
        _fact(
            id="f_doc_26_014",
            predicate="trauma_history",
            value="exposure to trauma",
            value_text="exposure to trauma and alleged in utero exposure to methamphetamines",
            source_id="doc_26",
            source_date="2013-09-10",
            as_of_date="2013-09-10",
        ),
        _fact(
            id="f_doc_26_005",
            predicate="behavioral_concern",
            value="meltdowns 2-5 times per week",
            value_text="meltdowns 2-5 times per week",
            source_id="doc_26",
            source_date="2013-09-10",
            as_of_date="2013-09-10",
        ),
        _fact(
            id="f_doc_26_012",
            predicate="behavioral_concern",
            value="borderline clinical range for emotional reactivity",
            value_text="borderline clinical range for emotional reactivity and oppositional defiant problems",
            source_id="doc_26",
            source_date="2013-09-10",
            as_of_date="2013-09-10",
        ),
    ]
    ledger = Ledger(
        child=Child(
            name="Emma Rose Callahan", dob="2010-03-22", evaluation_date="2025-07-11"
        ),
        ledger_version="1",
        built_at="2025-07-11T00:00:00Z",
        sources=sources,
        facts=facts,
    )

    birth = select_birth_developmental_history(ledger)
    birth_ids = {f.id for f in birth.facts}
    assert "f_doc_11_006" not in birth_ids
    assert "f_walk" in birth_ids

    health = select_health_history(ledger)
    health_ids = {f.id for f in health.facts}
    assert "f_doc_13_005" not in health_ids  # future-dated → review, not eligible
    assert "f_doc_21_003" not in health_ids
    assert "f_health_ok" in health_ids
    assert any(r.fact_id == "f_doc_13_005" for r in health.review_queue)

    prior = select_previous_evaluations(ledger)
    prior_ids = {f.id for f in prior.facts}
    assert "f_doc_26_001" not in prior_ids
    assert "f_doc_26_002" not in prior_ids
    assert "f_doc_26_005" not in prior_ids  # raw symptom dump
    assert "f_doc_26_014" in prior_ids
    assert "f_walk" in prior_ids
    assert "f_doc_26_012" in prior_ids  # instrument-result language

    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    assert any(e.fact_id == "f_doc_11_006" for e in plan.exclusions)
    assert any(e.fact_id == "f_doc_13_005" for e in plan.review_queue)
    md = render_evidence_brief_markdown(
        plan,
        next(s for s in plan.sections if s.section_key == "current_status_history"),
        ledger,
    )
    assert "f_doc_11_006" not in md.split("## Birth")[1].split("## ")[0] if "## Birth" in md else True
    assert "Review queue" in md or "f_doc_13_005" in md


if __name__ == "__main__":
    tests = [
        test_academic_weakness_not_developmental_history,
        test_behavioral_support_not_health_plan,
        test_transient_fatigue_not_sleep_vs_explicit_sleep_report,
        test_selectors_gate_smoke_failure_patterns,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
