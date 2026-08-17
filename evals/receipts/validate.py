"""Deterministic validators for disposition accounting and parent acceptance."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from evals.receipts.models import BriefDisposition, ExtractDisposition, LineageKind
from evals.receipts.store import ReceiptStore


class AccountingError(ValueError):
    """Disposition / total-accounting invariant failure."""


FORBIDDEN_GENERIC_EXCLUDED = frozenset({"excluded", "dropped", "skipped", "silenced"})
DIAGNOSTIC_LINEAGES = frozenset({"diagnostic_replay", "legacy_untraceable"})
EVALUABLE_DISPOSITIONS = frozenset(
    {
        "retained",
        "transformed",
        "suppressed_duplicate",
        "quarantined",
        "not_draftable",
        "error",
    }
)


def assert_no_generic_excluded(kinds: Iterable[str]) -> None:
    bad = [k for k in kinds if k in FORBIDDEN_GENERIC_EXCLUDED]
    if bad:
        raise AccountingError(
            f"generic drop dispositions are forbidden: {bad}; "
            "use quarantined / not_draftable / suppressed_duplicate / error "
            "(or observed_silent_drop only on diagnostic lineage)"
        )


def validate_extract_dispositions(
    item_ids: list[str],
    dispositions: list[ExtractDisposition],
    *,
    lineage: LineageKind | str = "evaluable",
) -> dict[str, int]:
    """Every raw item_id has exactly one terminal disposition."""

    assert_no_generic_excluded(d.kind for d in dispositions)
    by_item: dict[str, list[ExtractDisposition]] = {}
    for d in dispositions:
        by_item.setdefault(d.item_id, []).append(d)

    missing = [i for i in item_ids if i not in by_item]
    if missing:
        raise AccountingError(f"unaccounted raw items: {missing}")

    extras = [i for i in by_item if i not in set(item_ids)]
    if extras:
        raise AccountingError(f"dispositions for unknown items: {extras}")

    for item_id, rows in by_item.items():
        if len(rows) != 1:
            raise AccountingError(
                f"item {item_id} has {len(rows)} dispositions; need exactly one"
            )

    silent = [d for d in dispositions if d.kind == "observed_silent_drop"]
    if silent and lineage not in DIAGNOSTIC_LINEAGES:
        raise AccountingError(
            "observed_silent_drop is forbidden on evaluable lineage; "
            "substantive heuristic rejection must quarantine"
        )

    retained_facts = {
        d.fact_id
        for d in dispositions
        if d.kind in {"retained", "transformed"} and d.fact_id
    }
    for d in dispositions:
        if d.kind == "suppressed_duplicate":
            if d.canonical_fact_id not in retained_facts:
                raise AccountingError(
                    f"duplicate {d.item_id} names missing canonical "
                    f"{d.canonical_fact_id}"
                )
        if d.kind == "quarantined" and not d.review_item_id:
            raise AccountingError(
                f"quarantine {d.item_id} missing review_item_id"
            )

    return dict(Counter(d.kind for d in dispositions))


def dispositions_block_evaluable_acceptance(
    dispositions: list[ExtractDisposition],
) -> bool:
    """True when any item still lacks a valid evaluable terminal disposition."""

    return any(d.kind == "observed_silent_drop" for d in dispositions)


def validate_brief_dispositions(
    fact_ids: list[str],
    dispositions: list[BriefDisposition],
) -> dict[str, int]:
    """Every ledger fact is selected/routed/held/deduplicated/not_draftable."""

    assert_no_generic_excluded(d.kind for d in dispositions)
    by_fact: dict[str, list[BriefDisposition]] = {}
    for d in dispositions:
        by_fact.setdefault(d.fact_id, []).append(d)

    missing = [f for f in fact_ids if f not in by_fact]
    if missing:
        raise AccountingError(f"unaccounted ledger facts: {missing}")

    for fact_id, rows in by_fact.items():
        if len(rows) != 1:
            raise AccountingError(
                f"fact {fact_id} has {len(rows)} disposition rows; need exactly one "
                "(multi-destination reuse belongs in destinations[])"
            )

    retained_selected = {
        d.fact_id for d in dispositions if d.kind == "selected"
    }
    for d in dispositions:
        if d.kind == "suppressed_duplicate":
            if d.canonical_fact_id not in retained_selected and d.canonical_fact_id not in set(
                fact_ids
            ):
                raise AccountingError(
                    f"duplicate fact {d.fact_id} names missing canonical "
                    f"{d.canonical_fact_id}"
                )

    return dict(Counter(d.kind for d in dispositions))


def validate_evaluable_child_parents(
    store: ReceiptStore,
    *,
    child_run_id: str,
    parents: list[dict],
    lineage: str,
) -> None:
    from evals.receipts.review import require_accepted_parent

    if lineage in {"diagnostic_replay", "legacy_untraceable", "non_evaluable_preview"}:
        return
    for parent in parents:
        if not parent.get("required_accepted", True):
            continue
        require_accepted_parent(
            store,
            run_id=parent.get("run_id") or child_run_id,
            artifact_id=parent["artifact_id"],
            expected_sha256=parent["sha256"],
        )
