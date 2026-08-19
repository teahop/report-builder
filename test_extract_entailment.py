"""Extract-stage §9.3 — topic-agnostic claim check. No live model."""

from __future__ import annotations

import json
from typing import Any

from derived import AGE_DERIVATION, COMPUTED_SOURCE_ID, REQUEST_SOURCE_ID
from draft_validators import claim_from_fact, validate_ledger_entailment
from provider import ModelProvider, StructuredResult
from schemas import (
    Child,
    EntailmentJudgment,
    ExtractRequest,
    Fact,
    Ledger,
    Source,
)

_CHILD = Child(name="Taylor Nguyen", dob="2010-03-22", evaluation_date="2025-07-11")

_ROSTER = "Student is listed in grade 11 on the roster. Homeroom 4."
_WIDGET = "Widget count this period: 12. No other status is recorded."


class _QuoteProvider(ModelProvider):
    """supported=true iff the claim's quoted span appears in the source text."""

    def __init__(self) -> None:
        self._client = None  # type: ignore[assignment]
        self.calls: list[dict] = []

    def complete_structured(self, **kwargs: Any) -> StructuredResult:  # type: ignore[override]
        user = json.loads(kwargs["user"])
        self.calls.append(user)
        content = (user.get("source") or {}).get("content") or ""
        claim = user.get("claim") or ""
        quoted = claim.split(". ", 1)[-1] if ". " in claim else claim
        supported = quoted.strip().lower() in content.lower()
        return StructuredResult(
            data=EntailmentJudgment(
                supported=supported,
                rationale="quoted span in source" if supported else "quoted span absent",
            ),
            total_tokens=10,
            prompt_tokens=8,
            completion_tokens=2,
        )


class _BoomProvider(ModelProvider):
    def __init__(self) -> None:
        self._client = None  # type: ignore[assignment]

    def complete_structured(self, **kwargs: Any) -> StructuredResult:  # type: ignore[override]
        raise RuntimeError("provider down")


def _source(content: str, *, source_id: str = "doc_x") -> Source:
    return Source(
        id=source_id,
        type="school",
        date="2023-09-18",
        label=source_id,
        content=content,
        doc_class="narrative",
    )


def _fact(**kwargs: Any) -> Fact:
    base: dict[str, Any] = dict(
        id="f_doc_x_001",
        subject="child",
        predicate="grade",
        value="11",
        value_text="Student is listed in grade 11 on the roster.",
        qualifier=None,
        assertion="asserted",
        source_id="doc_x",
        source_date="2023-09-18",
        as_of_date="2023-09-18",
        reporter=None,
        life_stage="current",
        grade="11",
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


def test_claim_is_built_from_fact_fields() -> None:
    fact = _fact(qualifier="period-2", assertion="denied", value="none")
    claim = claim_from_fact(fact)
    assert "grade" in claim
    assert "(period-2)" in claim
    assert "is not none." in claim
    assert "Student is listed in grade 11 on the roster." in claim


def test_unsupported_claim_is_listed_and_fact_stays() -> None:
    source = _source(_WIDGET)
    fact = _fact(
        value="complete",
        value_text="Work is complete with no outstanding items.",
    )
    ledger = _ledger(source, [fact])
    provider = _QuoteProvider()
    findings, total, _, _ = validate_ledger_entailment(
        provider, model="gpt-4o-mini", ledger=ledger
    )
    assert findings
    assert findings[0].fact_id == fact.id
    assert "Work is complete with no outstanding items." in findings[0].claim
    assert ledger.facts[0].id == fact.id
    assert ledger.facts[0].value_text == fact.value_text
    assert total == 10
    assert provider.calls


def test_near_quote_claim_is_not_listed() -> None:
    source = _source(_ROSTER)
    fact = _fact()
    findings, _, _, _ = validate_ledger_entailment(
        _QuoteProvider(), model="gpt-4o-mini", ledger=_ledger(source, [fact])
    )
    assert findings == []


def test_derived_and_request_rows_are_not_checked() -> None:
    source = _source(_WIDGET)
    computed = _fact(
        id="f_computed_age_years",
        predicate="age_years",
        value="15",
        value_text="Age 15 years at evaluation",
        source_id=COMPUTED_SOURCE_ID,
        derivation=AGE_DERIVATION,
        grade=None,
    )
    request = _fact(
        id="f_request_dob",
        predicate="dob",
        value="2010-03-22",
        value_text="DOB on referral/intake form: 2010-03-22",
        source_id=REQUEST_SOURCE_ID,
        grade=None,
        temporality="durable",
        life_stage="birth",
    )
    invented = _fact(
        id="f_doc_x_002",
        value="complete",
        value_text="Work is complete with no outstanding items.",
    )
    ledger = Ledger(
        child=_CHILD,
        ledger_version="test",
        built_at="2026-08-19T00:00:00Z",
        sources=[source],
        facts=[computed, request, invented],
    )
    provider = _QuoteProvider()
    findings, _, _, _ = validate_ledger_entailment(
        provider, model="gpt-4o-mini", ledger=ledger
    )
    assert [c["source"]["id"] for c in provider.calls] == ["doc_x"]
    assert [f.fact_id for f in findings] == ["f_doc_x_002"]
    assert {fact.id for fact in ledger.facts} == {
        "f_computed_age_years",
        "f_request_dob",
        "f_doc_x_002",
    }


def test_prior_source_facts_are_not_rechecked() -> None:
    kept = _source(_WIDGET, source_id="doc_old")
    fresh = _source(_ROSTER, source_id="doc_new")
    old_fact = _fact(
        id="f_doc_old_001",
        source_id="doc_old",
        value="complete",
        value_text="Work is complete with no outstanding items.",
    )
    new_fact = _fact(id="f_doc_new_001", source_id="doc_new")
    ledger = Ledger(
        child=_CHILD,
        ledger_version="test",
        built_at="2026-08-19T00:00:00Z",
        sources=[kept, fresh],
        facts=[old_fact, new_fact],
    )
    provider = _QuoteProvider()
    findings, _, _, _ = validate_ledger_entailment(
        provider,
        model="gpt-4o-mini",
        ledger=ledger,
        source_ids={"doc_new"},
    )
    assert [c["source"]["id"] for c in provider.calls] == ["doc_new"]
    assert findings == []


def test_check_exception_is_a_finding_not_a_raise() -> None:
    source = _source(_ROSTER)
    fact = _fact()
    findings, total, _, _ = validate_ledger_entailment(
        _BoomProvider(), model="gpt-4o-mini", ledger=_ledger(source, [fact])
    )
    assert findings
    assert findings[0].fact_id == fact.id
    assert "provider down" in findings[0].rationale
    assert total == 0
    assert _ledger(source, [fact]).facts[0].id == fact.id


def test_extract_request_skip_entailment_defaults_false() -> None:
    body = ExtractRequest(
        confirm_synthetic=True,
        child=_CHILD,
        sources=[_source(_ROSTER)],
    )
    assert body.skip_entailment is False
    assert body.entailment_model == "gpt-4o-mini"


if __name__ == "__main__":
    tests = [
        test_claim_is_built_from_fact_fields,
        test_unsupported_claim_is_listed_and_fact_stays,
        test_near_quote_claim_is_not_listed,
        test_derived_and_request_rows_are_not_checked,
        test_prior_source_facts_are_not_rechecked,
        test_check_exception_is_a_finding_not_a_raise,
        test_extract_request_skip_entailment_defaults_false,
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
