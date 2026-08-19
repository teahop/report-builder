"""Hard rule 2 — mixed serial list in one span with no sibling facts. No live model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas import Child, Fact, Ledger, Source
from undersplit import (
    detect_undersplit_facts,
    is_heterogeneous_serial_list,
    stamp_undersplit_flags,
)

_DIR = Path(__file__).resolve().parent
_CACHE = _DIR / "evals" / "cache" / "fixture_001_ledger.json"
_CHILD = Child(name="Taylor Nguyen", dob="2010-03-22", evaluation_date="2025-07-11")

# Topic-free packing: mixed item shapes, three+ serial items.
_PACKED = (
    "According to the intake completed on 4/10/19 by a parent, the student has "
    "a history of widgets, a sensitivity to sprockets, gasket problems, and seasonal gears."
)
_PACKED_VALUE = (
    "history of widgets, a sensitivity to sprockets, gasket problems, and seasonal gears"
)
_MEDS = "She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night."
_CLEAN = "Student is listed in grade 11 on the roster."


def _source(content: str, *, source_id: str = "doc_x") -> Source:
    return Source(
        id=source_id,
        type="parent",
        date="2019-04-10",
        label=source_id,
        content=content,
        doc_class="narrative",
    )


def _fact(**kwargs: Any) -> Fact:
    base: dict[str, Any] = dict(
        id="f_doc_x_001",
        subject="child",
        predicate="behavioral_concern",
        value=_PACKED_VALUE,
        value_text=_PACKED,
        qualifier=None,
        assertion="asserted",
        source_id="doc_x",
        source_date="2019-04-10",
        as_of_date="2019-04-10",
        reporter=None,
        life_stage="current",
        grade=None,
        temporality="as_of",
        confidence="stated",
        derivation=None,
        inherits_dispute=False,
        valence="concern",
        source_section=None,
    )
    base.update(kwargs)
    return Fact.model_validate(base)


def _ledger(source: Source, facts: list[Fact]) -> Ledger:
    return Ledger(
        child=_CHILD,
        ledger_version="test",
        built_at="2026-08-19T00:00:00Z",
        sources=[source],
        facts=facts,
    )


def test_heterogeneous_serial_list_is_the_signal() -> None:
    assert is_heterogeneous_serial_list(_PACKED)
    assert not is_heterogeneous_serial_list(_MEDS)
    assert not is_heterogeneous_serial_list(_CLEAN)
    assert not is_heterogeneous_serial_list("She is kind, helpful, and engaged.")


def test_packed_span_with_no_siblings_is_flagged() -> None:
    ledger, findings = stamp_undersplit_flags(_ledger(_source(_PACKED), [_fact()]))
    assert findings
    assert findings[0].fact_id == "f_doc_x_001"
    assert ledger.facts[0].needs_claim_split is True


def test_homogeneous_dose_list_is_not_flagged() -> None:
    fact = _fact(
        predicate="medications",
        value="guanfacine, singular, melatonin",
        value_text=_MEDS,
        valence="neutral",
    )
    _, findings = stamp_undersplit_flags(_ledger(_source(_MEDS), [fact]))
    assert findings == []
    assert fact.needs_claim_split is False


def test_already_split_siblings_are_not_flagged() -> None:
    source = _source(_PACKED)
    facts = [
        _fact(
            id="f_doc_x_001",
            value="widgets",
            value_text="a history of widgets",
        ),
        _fact(
            id="f_doc_x_002",
            predicate="sleep",
            value="gasket problems",
            value_text="gasket problems",
        ),
        _fact(
            id="f_doc_x_003",
            predicate="allergy_status",
            value="seasonal gears",
            value_text="seasonal gears",
        ),
    ]
    _, findings = stamp_undersplit_flags(_ledger(source, facts))
    assert findings == []


def test_clean_single_claim_sentence_is_not_flagged() -> None:
    fact = _fact(
        predicate="grade",
        value="11",
        value_text=_CLEAN,
        valence="neutral",
        temporality="as_of",
    )
    _, findings = stamp_undersplit_flags(_ledger(_source(_CLEAN), [fact]))
    assert findings == []


def test_cached_parent_detector_runs() -> None:
    """New parent is valid input; packing catch is the synthetic tests above."""

    payload = json.loads(_CACHE.read_text(encoding="utf-8"))
    ledger = Ledger.model_validate(payload["ledger"])
    assert ledger.child.name == "Emma Rose Callahan"
    findings = detect_undersplit_facts(ledger)
    assert isinstance(findings, list)
    flagged = {item.fact_id for item in findings}
    assert flagged <= {f.id for f in ledger.facts}
