"""Held-back Case 001 / 005 input-sufficiency checks — no example-report targets."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Callable

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from referral_context import prepare_referral_context
from referral_schemas import ReferralContext
from schemas import Ledger

_CACHE = _WEEK1 / "evals" / "cache"
# report-builder/ sits at the workspace root.
_WORKSPACE_ROOT = _WEEK1.parent
_EXAMPLE_REPORTS = _WORKSPACE_ROOT / "data" / "approved-anonymized" / "example-reports"


def refuse_example_reports(path: Path) -> None:
    resolved = path.resolve()
    if "example-reports" in resolved.parts:
        raise RuntimeError(
            f"Refusing example-reports path in referral evals: {resolved}"
        )


def _load_cached_ledger(cache_name: str) -> Ledger:
    path = _CACHE / cache_name
    refuse_example_reports(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    ledger_obj = raw["ledger"] if "ledger" in raw else raw
    return Ledger.model_validate(ledger_obj)


def test_contamination_guard_refuses_example_reports() -> None:
    decoy = Path("/tmp/example-reports/case-001-final.md")
    try:
        refuse_example_reports(decoy)
    except RuntimeError as exc:
        assert "example-reports" in str(exc)
        return
    raise AssertionError("expected RuntimeError")


def test_example_reports_dir_never_read_by_this_module() -> None:
    if _EXAMPLE_REPORTS.exists():
        try:
            refuse_example_reports(_EXAMPLE_REPORTS / "any.md")
        except RuntimeError:
            return
        raise AssertionError("expected RuntimeError")


def test_case_001_source_only_preflight_surfaces_missing_intake() -> None:
    ledger = _load_cached_ledger("fixture_001_ledger.json")
    pre = prepare_referral_context(ledger, ReferralContext())

    assert pre.ready_for_draft is False
    missing = {i.field for i in pre.missing_fields}
    assert "evaluation_type" in missing
    assert "referral_trigger" in missing
    assert pre.selected_context.referral_trigger is None
    assert pre.selected_context.client_goals == []
    assert pre.selected_context.relevant_existing_diagnoses == []

    rr_facts = [f for f in ledger.facts if f.predicate == "referral_reason"]
    if rr_facts:
        assert pre.candidate_fields
        assert all(
            "unconfirmed candidates only" in c.reason for c in pre.candidate_fields
        )


def test_case_001_does_not_treat_iep_history_as_referral_trigger() -> None:
    ledger = _load_cached_ledger("fixture_001_ledger.json")
    pre = prepare_referral_context(ledger, ReferralContext())
    assert pre.selected_context.referral_trigger is None
    for c in pre.candidate_fields:
        assert c.confirmation_state == "not_yet_collected"
        assert c.requires_clinician_selection is True


def test_case_005_source_only_marks_confirmation_work() -> None:
    ledger = _load_cached_ledger("fixture_005_ledger_pruned.json")
    pre = prepare_referral_context(ledger, ReferralContext())

    assert pre.ready_for_draft is False
    missing = {i.field for i in pre.missing_fields}
    assert "evaluation_type" in missing
    assert "referral_trigger" in missing
    assert "requested_by" in missing

    rr_facts = [f for f in ledger.facts if f.predicate == "referral_reason"]
    assert rr_facts
    assert pre.candidate_fields
    assert pre.selected_context.referral_trigger is None
    assert pre.selected_context.areas_of_disagreement == []
    assert pre.selected_context.suspected_disabilities == []
    assert ledger.child.name
    assert pre.selected_context.evaluation_type is None


def test_case_005_misrouted_diagnosis_stays_candidate() -> None:
    ledger = _load_cached_ledger("fixture_005_ledger_pruned.json")
    pre = prepare_referral_context(ledger, ReferralContext())
    assert pre.selected_context.relevant_existing_diagnoses == []
    assert pre.selected_context.referral_trigger is None
    assert pre.candidate_fields


TESTS: list[tuple[str, Callable[[], None]]] = [
    (name, fn)
    for name, fn in globals().items()
    if name.startswith("test_") and callable(fn)
]


def main() -> int:
    print("=== Referral acceptance (source-only) ===")
    results: list[tuple[str, bool]] = []
    for name, fn in TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
            results.append((name, True))
        except Exception as exc:
            print(f"  FAIL  {name}: {exc}")
            traceback.print_exc()
            results.append((name, False))
    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
