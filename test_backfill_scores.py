"""Grade backfill — reading grades out of the two places they live.

Scores are the only thing Langfuse lets you attach to a trace after the fact, so
these are the path by which past runs become measurable at all.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.backfill_scores import (
    SCORE_BLOCK_PASS_RATE,
    SCORE_HUMAN_LABEL,
    SCORE_HUMAN_PASS,
    Score,
    _as_pass_fail,
    automated_scores,
    workbook_scores,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("PASS", True),
        ("pass", True),
        ("Y", True),
        (1, True),
        ("FAIL", False),
        ("n", False),
        (0, False),
        ("", None),
        (None, None),
        ("maybe", None),
    ],
)
def test_pass_fail_words(raw: object, expected: bool | None) -> None:
    assert _as_pass_fail(raw) is expected


def test_score_id_is_stable_and_distinct() -> None:
    first = Score("trace-1", "human_pass", 1.0, "BOOLEAN", None, "open_coding")
    same = Score("trace-1", "human_pass", 0.0, "BOOLEAN", "notes", "open_coding")
    other_trace = Score("trace-2", "human_pass", 1.0, "BOOLEAN", None, "open_coding")
    other_source = Score("trace-1", "human_pass", 1.0, "BOOLEAN", None, "panel_checks")

    # Same trace + name + source ⇒ same id, so a re-run updates in place.
    assert first.score_id == same.score_id
    assert first.score_id != other_trace.score_id
    assert first.score_id != other_source.score_id


def test_automated_scores_from_a_history_trace(tmp_path: Path) -> None:
    path = tmp_path / "traces" / "sweep-test.jsonl"
    path.parent.mkdir()
    rows = [
        {
            "trace_id": "aaa",
            "status": "ok",
            "blocks": [{"prose": "Emma attends a comprehensive high school."}],
            "prose": "Emma attends a comprehensive high school.",
        },
        {
            "trace_id": "bbb",
            "status": "ok",
            "blocks": [{"prose": "Emma is a 10-year-old female."}],
            "prose": "Emma is a 10-year-old female. Overall, a complex history.",
        },
        {"trace_id": "ccc", "status": "error"},
        {"status": "ok", "prose": "no trace id, cannot be attached"},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    scores = automated_scores(path)
    by_trace = {(s.trace_id, s.name): s.value for s in scores}

    assert by_trace[("aaa", "no_dob_age_opener")] == 1.0
    assert by_trace[("bbb", "no_dob_age_opener")] == 0.0
    assert by_trace[("bbb", "no_summarative_register")] == 0.0
    # Failed runs and rows with no trace id have nothing to attach to.
    assert not any(s.trace_id == "ccc" for s in scores)
    assert all(s.trace_id for s in scores)


def _write_workbook(path: Path, drafts: list[tuple], blocks: list[tuple]) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    sheet = wb.active
    sheet.title = "Drafts"
    sheet.append(["#", "trace_id", "url", "fixture", "run", "labels", "prose", "quotes", "notes", "pass", "label"])
    for row in drafts:
        sheet.append(list(row))
    blocks_sheet = wb.create_sheet("Blocks")
    blocks_sheet.append(["#", "trace_id", "fixture", "run", "block", "prose", "facts", "notes", "pass", "label"])
    for row in blocks:
        blocks_sheet.append(list(row))
    wb.save(path)


def test_workbook_scores_reads_the_yellow_columns(tmp_path: Path) -> None:
    path = tmp_path / "sweep-test.xlsx"
    _write_workbook(
        path,
        drafts=[
            (1, "aaa", "", "fixture_001", 1, "", "", 0, "opens flat", "PASS", "clean opener"),
            (2, "bbb", "", "fixture_001", 2, "", "", 1, "", "FAIL", "summarative"),
            (3, "ccc", "", "fixture_001", 3, "", "", 0, "", "", ""),
        ],
        blocks=[
            (1, "aaa", "fixture_001", 1, "Family History", "", "", "", "PASS", ""),
            (2, "aaa", "fixture_001", 1, "Birth History", "", "", "", "FAIL", ""),
            (3, "bbb", "fixture_001", 2, "Family History", "", "", "", "FAIL", ""),
        ],
    )

    scores = workbook_scores(path)
    indexed = {(s.trace_id, s.name): s for s in scores}

    assert indexed[("aaa", SCORE_HUMAN_PASS)].value == 1.0
    assert indexed[("aaa", SCORE_HUMAN_PASS)].comment == "opens flat"
    assert indexed[("bbb", SCORE_HUMAN_PASS)].value == 0.0
    assert indexed[("bbb", SCORE_HUMAN_LABEL)].value == "summarative"
    assert indexed[("aaa", SCORE_BLOCK_PASS_RATE)].value == 0.5
    assert indexed[("bbb", SCORE_BLOCK_PASS_RATE)].value == 0.0
    # An ungraded row contributes nothing rather than a false zero.
    assert not any(s.trace_id == "ccc" for s in scores)


def test_ungraded_workbook_yields_no_scores(tmp_path: Path) -> None:
    path = tmp_path / "sweep-blank.xlsx"
    _write_workbook(
        path,
        drafts=[(1, "aaa", "", "fixture_001", 1, "", "", 0, "", "", "")],
        blocks=[(1, "aaa", "fixture_001", 1, "Family History", "", "", "", "", "")],
    )
    assert workbook_scores(path) == []
