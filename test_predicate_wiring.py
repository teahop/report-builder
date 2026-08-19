"""No silent disposition: every registered predicate is selected, header-only, provenance, or listed."""

from __future__ import annotations

from history_evidence import HEADER_ONLY_PREDICATES
from history_selectors import (
    DELIBERATELY_UNWIRED_PREDICATES,
    headed_selector_predicates,
)
from predicates import PREDICATE_VOCABULARY, PROVENANCE_PREDICATES


def test_every_registered_predicate_has_a_disposition() -> None:
    registered = {spec.name for spec in PREDICATE_VOCABULARY}
    accounted = (
        headed_selector_predicates()
        | HEADER_ONLY_PREDICATES
        | PROVENANCE_PREDICATES
        | frozenset(DELIBERATELY_UNWIRED_PREDICATES)
    )
    missing = registered - accounted
    assert missing == set(), (
        "registered predicates with no selector, header-only, provenance, "
        f"or deliberately-unwired reason: {sorted(missing)}"
    )


def test_deliberately_unwired_entries_have_reasons() -> None:
    for name, reason in DELIBERATELY_UNWIRED_PREDICATES.items():
        assert reason.strip(), f"{name} is unwired with an empty reason"


def test_unwired_reason_cannot_replace_a_selector() -> None:
    overlap = headed_selector_predicates() & frozenset(DELIBERATELY_UNWIRED_PREDICATES)
    assert overlap == set(), f"listed as unwired but also selected: {sorted(overlap)}"