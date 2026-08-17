"""Focused offline tests for evals/panel_checks.py — real referral traces, no model calls."""

from __future__ import annotations

import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parent
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.panel_checks import (
    AFTER_STAMP,
    BEFORE_STAMP,
    CHECK_DOB_AGE_OPENER,
    CHECK_QUOTE_POLICY,
    CHECK_SUMMARATIVE,
    all_checks_passed,
    before_after_deltas,
    find_trace_by_stamp,
    history_before_after,
    list_trace_files,
    load_taxonomy,
    load_trace,
    score_history_record,
    score_referral_record,
    trace_kind,
)


def _require(path: Path | None, stamp: str) -> Path:
    assert path is not None, f"missing referral trace for stamp {stamp}"
    return path


def test_lists_referral_and_history_jsonl_only() -> None:
    paths = list_trace_files()
    names = {p.name for p in paths}
    assert "smoke-20260810-181712.jsonl" in names
    assert "smoke-20260810-183119.jsonl" in names
    assert "smoke-20260810-190139.jsonl" in names
    assert "smoke-20260810-200554.jsonl" in names
    assert "smoke-20260810-201247.jsonl" in names
    assert all(p.suffix == ".jsonl" for p in paths)
    kinds = {trace_kind(p) for p in paths}
    assert kinds == {"referral", "history"}


def test_pre_fix_181712_fails_at_least_one_check() -> None:
    path = _require(find_trace_by_stamp(BEFORE_STAMP), BEFORE_STAMP)
    loaded = load_trace(path)
    assert loaded.kind == "referral"
    assert loaded.records
    results = score_referral_record(loaded.records[0])
    assert len(results) == 4
    assert not all_checks_passed(results)
    quote = next(item for item in results if item.name == CHECK_QUOTE_POLICY)
    assert quote.passed is False


def test_accepted_190139_passes_all_checks() -> None:
    path = _require(find_trace_by_stamp(AFTER_STAMP), AFTER_STAMP)
    loaded = load_trace(path)
    assert loaded.kind == "referral"
    results = score_referral_record(loaded.records[0])
    assert all_checks_passed(results), [item.detail for item in results if not item.passed]


def test_validation_failed_183119_is_scored_and_fails() -> None:
    path = _require(find_trace_by_stamp("183119"), "183119")
    loaded = load_trace(path)
    record = loaded.records[0]
    assert record.get("status") == "validation_failed"
    results = score_referral_record(record)
    assert not all_checks_passed(results)


def test_before_after_quote_policy_moves() -> None:
    before = load_trace(_require(find_trace_by_stamp(BEFORE_STAMP), BEFORE_STAMP))
    after = load_trace(_require(find_trace_by_stamp(AFTER_STAMP), AFTER_STAMP))
    rows = before_after_deltas(
        score_referral_record(before.records[0]),
        score_referral_record(after.records[0]),
    )
    quote_row = next(row for row in rows if row["check"] == CHECK_QUOTE_POLICY)
    assert quote_row["delta"] == "fail → pass"


def test_history_traces_score_opener_and_keep_kind() -> None:
    history = [p for p in list_trace_files() if trace_kind(p) == "history"]
    assert len(history) >= 2
    for path in history:
        loaded = load_trace(path)
        assert loaded.kind == "history"
        assert loaded.records
        results = score_history_record(loaded.records[0])
        names = {item.name for item in results}
        assert names == {CHECK_DOB_AGE_OPENER, CHECK_SUMMARATIVE}


def test_history_diagnostic_smokes_opener_passes() -> None:
    for stamp in ("200554", "201247"):
        path = find_trace_by_stamp(stamp, kind="history")
        assert path is not None, stamp
        results = score_history_record(load_trace(path).records[0])
        opener = next(item for item in results if item.name == CHECK_DOB_AGE_OPENER)
        assert opener.passed is True, opener.detail


def test_history_before_after_opener_moves() -> None:
    comparison = history_before_after()
    assert comparison.before_source == "coded"
    assert comparison.before_record is not None
    prose = comparison.before_record.get("prose") or ""
    assert "born on March 22, 2010" in prose
    assert comparison.after_path is not None
    assert "sweep-20260814" in comparison.after_path.name
    opener = next(row for row in comparison.deltas if row["check"] == CHECK_DOB_AGE_OPENER)
    assert opener["before"] == "fail"
    assert opener["after"] == "pass"
    assert opener["delta"] == "fail → pass"
    after_opener = next(
        item for item in comparison.after_results if item.name == CHECK_DOB_AGE_OPENER
    )
    assert after_opener.n_pass == 20
    assert after_opener.n == 20
    summarative = next(row for row in comparison.deltas if row["check"] == CHECK_SUMMARATIVE)
    assert summarative["check"] == CHECK_SUMMARATIVE
    assert summarative["after"] == "fail"


def test_taxonomy_uses_coded_history_categories() -> None:
    data = load_taxonomy()
    assert data["source"] == "Langfuse session sweep-20260807-132534-c9e20e"
    assert data["rows"]
    categories = [row["category"] for row in data["rows"]]
    assert "opens with DOB/age + overly summarative register" in categories
    for row in data["rows"]:
        assert "count" in row
        assert "example_note" in row
