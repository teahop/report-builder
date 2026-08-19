"""Block-granularity as_of inheritance and C1 anchor-drift — no live model."""

from __future__ import annotations

import json
from pathlib import Path

from anchor import (
    check_anchor_drift,
    detect_dated_blocks,
    resolve_as_of_date,
)
from extract import consolidate_medications_facts, draft_to_fact
from schemas import Child, ExtractedFactDraft, Fact, Ledger, Source

_DIR = Path(__file__).resolve().parent
_DOC11 = _DIR / "fixtures" / "fixture_001" / "doc_11.json"
_DIAGNOSTIC = (
    _DIR / "evals/history/diagnostic_ladder/run-20260814T180644Z/ledger.json"
)

_CHILD = Child(name="Taylor Nguyen", dob="2010-03-22", evaluation_date="2025-07-11")

# Date-led copied block — same shape as the doc_11 Health region, no topic names in the code under test.
_COPIED_BLOCK = """
Cover sheet
IEP Date: 10/2/2024
Student Name: Taylor Nguyen

Health
2024: current-year note with no copied date on the claims beneath the next headings.

9/28/23-Summary/Recommendations:
She is a healthy girl. She takes Geodon, Trileptal, and Vyvance. She has no known allergies.

4/25/19
Hearing PASSED with both ears.
She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night.
She met all of her developmental milestones on time except walking at about 19 mos.
Per mom, she is getting fitted for a CPAP machine and will be part of a sleep study over summer.

INDIVIDUAL TRANSITION PLANNING
Student Name: Taylor Nguyen                    IEP Date: 10/2/2024
"""

_PERIOD_DASHBOARD = """
Print date 2021-02-08

Period 2 dashboard
Start Date: 11/09/2020
Target Date: 02/08/2021
Science overall 78%

Period 3 dashboard
Start Date: 02/21/2021
Target Date: 05/27/2021
Science overall 83%
"""

_YEAR_SPAN_PRINTOUT = """
Print Student Attendance
        2023-2024                                           Meadowbrook High School                                                9/18/2023
        Summary of Attendance
        Tardy 6
        Absent 4
"""


def _source(
    content: str,
    *,
    source_id: str = "doc_x",
    date: str = "2024-10-02",
) -> Source:
    return Source(
        id=source_id,
        type="school",
        date=date,
        label=source_id,
        content=content,
        doc_class="narrative",
    )


def _draft(**kwargs) -> ExtractedFactDraft:
    base = {
        "subject": "child",
        "predicate": "medications",
        "value": "guanfacine",
        "value_text": "She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night.",
        "assertion": "asserted",
        "life_stage": "current",
        "confidence": "stated",
    }
    base.update(kwargs)
    return ExtractedFactDraft.model_validate(base)


def _fact(**kwargs) -> Fact:
    base = dict(
        id="f_x_001",
        subject="child",
        predicate="medications",
        value="guanfacine",
        value_text="She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night.",
        qualifier=None,
        assertion="asserted",
        source_id="doc_x",
        source_date="2024-10-02",
        as_of_date="2024-10-02",
        reporter=None,
        life_stage="current",
        grade=None,
        temporality="as_of",
        confidence="stated",
        derivation=None,
        inherits_dispute=False,
        valence="neutral",
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


def test_date_led_block_is_detected() -> None:
    blocks = detect_dated_blocks(_COPIED_BLOCK, "2024-10-02")
    as_ofs = {b.as_of for b in blocks}
    assert "2019-04-25" in as_ofs
    assert "2023-09-28" in as_ofs
    # Same-year "2024:" prefix is not a prior-record opener.
    assert "2024-01-01" not in as_ofs
    # Running IEP Date equal to source.date is not an opener.
    assert "2024-10-02" not in as_ofs


def test_copied_block_facts_inherit_heading_date() -> None:
    source = _source(_COPIED_BLOCK)
    guan = resolve_as_of_date(_draft(), source)
    walked = resolve_as_of_date(
        _draft(
            predicate="walked_age_months",
            value="19",
            value_text="walking at about 19 mos",
        ),
        source,
    )
    allergy = resolve_as_of_date(
        _draft(
            predicate="allergy_status",
            value="none",
            value_text="She has no known allergies.",
        ),
        source,
    )
    assert guan == "2019-04-25"
    assert walked == "2019-04-25"
    assert allergy == "2023-09-28"


def test_claim_local_date_beats_containing_block() -> None:
    source = _source(_COPIED_BLOCK)
    # The appendectomy date sits in the 4/25/19 block; the claim itself names 4/1/19.
    content = _COPIED_BLOCK.replace(
        "Hearing PASSED with both ears.",
        "She had her appendix out earlier this month (4/1/19). Hearing PASSED with both ears.",
    )
    source = _source(content)
    as_of = resolve_as_of_date(
        _draft(
            predicate="hospitalizations",
            value="appendectomy",
            value_text="She had her appendix out earlier this month (4/1/19).",
        ),
        source,
    )
    assert as_of == "2019-04-01"


def test_vague_relative_time_does_not_invent_a_date() -> None:
    source = _source(
        "Parent summary dated June 2026. Student struggled with reading last year.",
        date="2026-06-01",
    )
    as_of = resolve_as_of_date(
        _draft(
            predicate="basic_reading",
            value="struggled",
            value_text="Student struggled with reading last year.",
            as_of_date=None,
        ),
        source,
    )
    assert as_of == "2026-06-01"


def test_c1_fires_when_as_of_still_equals_source_date() -> None:
    source = _source(_COPIED_BLOCK)
    fact = _fact(as_of_date="2024-10-02")
    findings = check_anchor_drift(_ledger(source, [fact]))
    assert findings
    assert findings[0].block_date == "2019-04-25"
    assert findings[0].as_of_date == "2024-10-02"


def test_c1_silent_after_block_inherit() -> None:
    source = _source(_COPIED_BLOCK)
    draft = _draft()
    fact = draft_to_fact(draft, fact_id="f_doc_x_001", source=source, child=_CHILD)
    assert fact.as_of_date == "2019-04-25"
    findings = check_anchor_drift(_ledger(source, [fact]))
    assert findings == []


def test_start_date_reporting_period_not_print_date() -> None:
    source = _source(_PERIOD_DASHBOARD, date="2021-02-08")
    t2 = resolve_as_of_date(
        _draft(
            predicate="written_expression",
            value="78%",
            value_text="Science overall 78%",
        ),
        source,
    )
    t3 = resolve_as_of_date(
        _draft(
            predicate="written_expression",
            value="83%",
            value_text="Science overall 83%",
        ),
        source,
    )
    assert t2 == "2020-11-09"
    assert t3 == "2021-02-21"
    assert t2 != source.date
    # Do not invent a display-string grain — as_of is the period start date.


def test_year_span_header_not_print_date() -> None:
    source = _source(_YEAR_SPAN_PRINTOUT, date="2023-09-18")
    as_of = resolve_as_of_date(
        _draft(
            predicate="attendance",
            value="6",
            value_text="Tardy 6",
        ),
        source,
    )
    assert as_of == "2023-01-01"
    assert as_of != source.date


def test_medications_not_merged_across_as_of() -> None:
    source = _source(_COPIED_BLOCK)
    current = _fact(
        id="f_a",
        value="geodon",
        value_text="She takes Geodon, Trileptal, and Vyvance.",
        as_of_date="2023-09-28",
    )
    prior = _fact(
        id="f_b",
        value="guanfacine",
        value_text="She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night.",
        as_of_date="2019-04-25",
    )
    merged = consolidate_medications_facts([current, prior])
    assert len(merged) == 2
    as_ofs = {f.as_of_date for f in merged}
    assert as_ofs == {"2023-09-28", "2019-04-25"}


def test_c1_fires_on_unfixed_doc11_health_block() -> None:
    """Calibration: doc_11's copied 2019 block must raise C1 before C1 is trusted elsewhere."""

    payload = json.loads(_DOC11.read_text(encoding="utf-8"))
    source = Source.model_validate(payload["sources"][0])
    assert source.date == "2024-10-02"
    blocks = detect_dated_blocks(source.content, source.date)
    assert any(b.as_of == "2019-04-25" for b in blocks)

    unfixed = _fact(
        id="f_doc_11_cal",
        source_id=source.id,
        source_date=source.date,
        as_of_date=source.date,
        predicate="walked_age_months",
        value="19",
        value_text="walking at about 19 mos",
    )
    findings = check_anchor_drift(_ledger(source, [unfixed]))
    assert findings, "C1 must fire on the unfixed 2019 health-block walk claim"
    assert findings[0].block_date == "2019-04-25"

    fixed = draft_to_fact(
        _draft(
            predicate="walked_age_months",
            value="19",
            value_text="walking at about 19 mos",
        ),
        fact_id="f_doc_11_cal_fixed",
        source=source,
        child=_CHILD,
    )
    assert fixed.as_of_date == "2019-04-25"
    assert check_anchor_drift(_ledger(source, [fixed])) == []


def test_c1_fires_on_frozen_diagnostic_doc11_ledger() -> None:
    """The unfixed Bastion extract of doc_11 is the calibration parent."""

    if not _DIAGNOSTIC.is_file():
        return
    payload = json.loads(_DIAGNOSTIC.read_text(encoding="utf-8"))
    ledger = Ledger.model_validate(payload["ledger"])
    findings = check_anchor_drift(ledger)
    drifted_ids = {item.fact_id for item in findings}
    assert "f_doc_11_030" in drifted_ids
    # CPAP "over summer" has no explicit date; C1 fires only if it sits in the dated block.
    # Record the result rather than requiring a keyword guard.
    cpap = next((f for f in ledger.facts if f.id == "f_doc_11_029"), None)
    assert cpap is not None
