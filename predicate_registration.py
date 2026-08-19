"""Checked predicate registration — a name cannot enter limbo silently.

Promotion still edits four sites by hand (vocabulary, selector frozenset,
HISTORY_PREDICATES, optional normalize rule). This module is the check that
those edits agree. It does not register vocabulary.

See docs/engineering/Predicate promotion — registration checklist.md.
"""

from __future__ import annotations

from coverage import HISTORY_PREDICATES
from history_evidence import HEADER_ONLY_PREDICATES
from history_selectors import (
    COVID_EDUCATIONAL_PREDICATES,
    DELIBERATELY_UNWIRED_PREDICATES,
    headed_selector_predicates,
)
from predicates import PREDICATE_VOCABULARY, PROVENANCE_PREDICATES

# Headed-selector names not declared on HISTORY_PREDICATES. A new registration
# must join HISTORY_PREDICATES rather than grow this dict. Reasons are required.
COVERAGE_UNDECLARED_PREDICATES: dict[str, str] = {
    "allergy_substance": (
        "Selected into Health History; coverage still keys on allergy_status."
    ),
    "behavioral_referral": (
        "Selected into School Experience; not yet a declared History expected."
    ),
    "family_history": (
        "Selected into Family History; not yet a declared History expected."
    ),
    "health_plan_status": (
        "Selected into Health History; not yet a declared History expected."
    ),
    "reading_level": (
        "Selected into School History / Experience; not yet a declared History expected."
    ),
    "school_enrollment": (
        "Selected into School History / Experience; not yet a declared History expected."
    ),
}


def accounted_predicates() -> frozenset[str]:
    """Every name a History consumer, header, provenance row, or explicit skip can read."""

    return (
        headed_selector_predicates()
        | HEADER_ONLY_PREDICATES
        | PROVENANCE_PREDICATES
        | frozenset(DELIBERATELY_UNWIRED_PREDICATES)
    )


def unconsumed_registered_predicates() -> frozenset[str]:
    """PREDICATE_VOCABULARY names with no selector, header, provenance, or skip reason."""

    registered = {spec.name for spec in PREDICATE_VOCABULARY}
    return frozenset(registered - accounted_predicates())


def coverage_declaration_gaps() -> frozenset[str]:
    """Selector names that are neither HISTORY_PREDICATES nor explicitly undeclared."""

    return frozenset(
        headed_selector_predicates()
        - HISTORY_PREDICATES
        - frozenset(COVERAGE_UNDECLARED_PREDICATES)
    )


def undeclared_empty_selector_sections() -> tuple[str, ...]:
    """Section frozensets left empty on purpose — not a per-predicate skip."""

    empty: list[str] = []
    if not COVID_EDUCATIONAL_PREDICATES:
        empty.append("COVID_EDUCATIONAL_PREDICATES")
    return tuple(empty)
