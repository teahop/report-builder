"""Type-aware re-assignment after a declared-shape mismatch. No live model."""

from __future__ import annotations

from typing import Any

from extract import (
    _held_for_shape_reassign,
    extract_source_to_facts,
)
from provider import ModelProvider, StructuredResult
from schemas import (
    Child,
    ExtractedFactDraft,
    Source,
    SourceExtraction,
)

_CHILD = Child(name="Taylor Nguyen", dob="2010-03-22", evaluation_date="2025-07-11")

_INCIDENT = (
    "After the recorded incident the student was frequently in the hallway. "
    "Widget inventory was not taken that afternoon."
)


class _SequenceProvider(ModelProvider):
    def __init__(self, outputs: list[SourceExtraction]) -> None:
        self._client = None  # type: ignore[assignment]
        self._outputs = list(outputs)
        self.systems: list[str] = []

    def complete_structured(self, **kwargs: Any) -> StructuredResult:  # type: ignore[override]
        self.systems.append(kwargs.get("system") or "")
        data = self._outputs.pop(0)
        return StructuredResult(
            data=data,
            total_tokens=20,
            prompt_tokens=16,
            completion_tokens=4,
        )


def _source(content: str = _INCIDENT) -> Source:
    return Source(
        id="doc_x",
        type="prior_eval",
        date="2023-01-19",
        label="doc_x",
        content=content,
        doc_class="narrative",
    )


def _draft(**kwargs: Any) -> ExtractedFactDraft:
    base = {
        "subject": "child",
        "predicate": "attendance",
        "value": "frequently in the hallway after the incident",
        "value_text": (
            "After the recorded incident the student was frequently in the hallway."
        ),
        "assertion": "asserted",
        "life_stage": "school-age",
        "confidence": "stated",
    }
    base.update(kwargs)
    return ExtractedFactDraft.model_validate(base)


def test_narrative_mismatch_is_held_for_reassign_not_unusable() -> None:
    source = _source()
    assert _held_for_shape_reassign(_draft(), source)


def test_shape_mismatch_is_reassigned_on_a_second_call() -> None:
    first = SourceExtraction(facts=[_draft()])
    second = SourceExtraction(
        facts=[
            _draft(
                predicate="behavioral_concern",
                value="hallway after incident",
                qualifier="conduct",
                valence="concern",
            )
        ]
    )
    provider = _SequenceProvider([first, second])
    facts, total, _, _ = extract_source_to_facts(
        provider, child=_CHILD, source=_source(), model="gpt-4o-mini"
    )
    assert len(provider.systems) == 2
    assert "declared value shapes" in provider.systems[1].lower()
    assert "bathroom" not in provider.systems[1].lower()
    assert "discipline" not in provider.systems[1].lower()
    predicates = [f.predicate for f in facts]
    assert "attendance" not in predicates
    assert "behavioral_concern" in predicates
    assert any("recorded incident" in (f.value_text or "") for f in facts)
    assert total == 40


def test_no_second_call_when_shapes_fit() -> None:
    first = SourceExtraction(
        facts=[
            _draft(
                predicate="grade",
                value="11",
                value_text="Grade 11",
            )
        ]
    )
    provider = _SequenceProvider([first])
    facts, _, _, _ = extract_source_to_facts(
        provider, child=_CHILD, source=_source("Grade 11"), model="gpt-4o-mini"
    )
    assert len(provider.systems) == 1
    assert [f.predicate for f in facts] == ["grade"]


def test_second_assignment_that_still_mismatches_is_dropped() -> None:
    first = SourceExtraction(facts=[_draft()])
    second = SourceExtraction(facts=[_draft()])  # still attendance + narrative
    provider = _SequenceProvider([first, second])
    facts, _, _, _ = extract_source_to_facts(
        provider, child=_CHILD, source=_source(), model="gpt-4o-mini"
    )
    assert len(provider.systems) == 2
    assert facts == []


if __name__ == "__main__":
    tests = [
        test_narrative_mismatch_is_held_for_reassign_not_unusable,
        test_shape_mismatch_is_reassigned_on_a_second_call,
        test_no_second_call_when_shapes_fit,
        test_second_assignment_that_still_mismatches_is_dropped,
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
