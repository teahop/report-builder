"""Push eval grades onto Langfuse traces that already exist.

Langfuse traces are immutable once written — there is no API to add tags,
session ids, or metadata after the fact. Scores are the exception: a score can
be attached to any trace at any time, by id. So a run that was made before
labeling shipped can still receive its grades, even though it can never receive
its labels.

Two sources of grades, and both land on the same traces:

  * **Automated** — the offline checks in ``evals/panel_checks.py``, recomputed
    from the stored JSONL. No model calls, no keys beyond Langfuse.
  * **Human** — the yellow columns of an open-coding workbook. The workbook's
    ``Drafts`` sheet carries the trace id in column B, so each row knows which
    trace it grades.

Idempotent: every score gets a deterministic id derived from
``(trace_id, score name, source)``, so re-running after grading ten more rows
updates rather than duplicates.

Usage::

    python evals/backfill_scores.py evals/coding/<sweep-id>.xlsx
    python evals/backfill_scores.py evals/traces/<sweep-id>.jsonl --auto-only
    python evals/backfill_scores.py evals/coding/<sweep-id>.xlsx --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

_WEEK1 = Path(__file__).resolve().parents[1]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from dotenv import load_dotenv

load_dotenv(_WEEK1 / ".env")

from evals.panel_checks import (  # noqa: E402
    load_trace_file,
    score_history_record,
    score_referral_record,
    trace_kind,
)

# Score names are the axis every chart is drawn against. Renaming one splits its
# trend line in two without warning, so they live here as constants and the
# workbook columns map onto them rather than inventing their own.
SCORE_HUMAN_PASS = "human_pass"
SCORE_HUMAN_LABEL = "human_label"
SCORE_BLOCK_PASS_RATE = "human_block_pass_rate"

_TRACE_DIRS = (
    _WEEK1 / "evals" / "traces",
    _WEEK1 / "evals" / "history" / "traces",
    _WEEK1 / "evals" / "referral" / "traces",
)

# Drafts sheet: A=#, B=trace_id, C=url, D=fixture, E=run, F=labels, G=prose,
# H=unanchored quotes, I=notes, J=pass/fail, K=label.
_DRAFTS_TRACE_COL = "B"
_DRAFTS_NOTES_COL = "I"
_DRAFTS_PASS_COL = "J"
_DRAFTS_LABEL_COL = "K"

# Blocks sheet: A=#, B=trace_id, …, H=notes, I=pass/fail, J=label.
_BLOCKS_TRACE_COL = "B"
_BLOCKS_PASS_COL = "I"

_PASS_WORDS = {"pass", "p", "yes", "y", "ok", "true", "1"}
_FAIL_WORDS = {"fail", "f", "no", "n", "false", "0"}


@dataclass(frozen=True)
class Score:
    trace_id: str
    name: str
    value: float | str
    data_type: Literal["NUMERIC", "CATEGORICAL", "BOOLEAN"]
    comment: str | None
    source: str

    @property
    def score_id(self) -> str:
        """Deterministic, so a re-run updates the same score instead of adding one."""

        digest = hashlib.sha256(
            f"{self.trace_id}:{self.name}:{self.source}".encode("utf-8")
        ).hexdigest()
        return digest[:32]


def _as_pass_fail(raw: Any) -> bool | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None
    if text in _PASS_WORDS:
        return True
    if text in _FAIL_WORDS:
        return False
    return None


def _matching_trace_file(workbook: Path) -> Path | None:
    """The JSONL a workbook was generated from — same stem, one of three dirs."""

    for folder in _TRACE_DIRS:
        candidate = folder / f"{workbook.stem}.jsonl"
        if candidate.is_file():
            return candidate
    return None


def automated_scores(trace_file: Path) -> list[Score]:
    records = load_trace_file(trace_file)
    kind = trace_kind(trace_file)
    scorer = score_referral_record if kind == "referral" else score_history_record

    scores: list[Score] = []
    for record in records:
        trace_id = record.get("trace_id")
        if not trace_id:
            continue
        if record.get("status") not in (None, "ok"):
            continue
        for result in scorer(record):
            scores.append(
                Score(
                    trace_id=str(trace_id),
                    name=result.name,
                    value=1.0 if result.passed else 0.0,
                    data_type="BOOLEAN",
                    comment=result.detail or None,
                    source="panel_checks",
                )
            )
    return scores


def workbook_scores(workbook: Path) -> list[Score]:
    from openpyxl import load_workbook

    wb = load_workbook(workbook, data_only=True)
    scores: list[Score] = []

    if "Drafts" in wb.sheetnames:
        sheet = wb["Drafts"]
        for row in range(2, sheet.max_row + 1):
            trace_id = sheet[f"{_DRAFTS_TRACE_COL}{row}"].value
            if not trace_id:
                continue
            trace_id = str(trace_id).strip()
            notes = sheet[f"{_DRAFTS_NOTES_COL}{row}"].value
            comment = str(notes).strip() if notes else None

            verdict = _as_pass_fail(sheet[f"{_DRAFTS_PASS_COL}{row}"].value)
            if verdict is not None:
                scores.append(
                    Score(
                        trace_id=trace_id,
                        name=SCORE_HUMAN_PASS,
                        value=1.0 if verdict else 0.0,
                        data_type="BOOLEAN",
                        comment=comment,
                        source="open_coding",
                    )
                )

            label = sheet[f"{_DRAFTS_LABEL_COL}{row}"].value
            if label and str(label).strip():
                scores.append(
                    Score(
                        trace_id=trace_id,
                        name=SCORE_HUMAN_LABEL,
                        value=str(label).strip(),
                        data_type="CATEGORICAL",
                        comment=comment,
                        source="open_coding",
                    )
                )

    if "Blocks" in wb.sheetnames:
        sheet = wb["Blocks"]
        tally: dict[str, list[bool]] = {}
        for row in range(2, sheet.max_row + 1):
            trace_id = sheet[f"{_BLOCKS_TRACE_COL}{row}"].value
            if not trace_id:
                continue
            verdict = _as_pass_fail(sheet[f"{_BLOCKS_PASS_COL}{row}"].value)
            if verdict is None:
                continue
            tally.setdefault(str(trace_id).strip(), []).append(verdict)
        for trace_id, verdicts in tally.items():
            scores.append(
                Score(
                    trace_id=trace_id,
                    name=SCORE_BLOCK_PASS_RATE,
                    value=round(sum(verdicts) / len(verdicts), 4),
                    data_type="NUMERIC",
                    comment=f"{sum(verdicts)}/{len(verdicts)} blocks pass",
                    source="open_coding_blocks",
                )
            )

    return scores


def post(scores: Iterable[Score], *, dry_run: bool) -> int:
    scores = list(scores)
    if not scores:
        print("nothing to post")
        return 0

    if dry_run:
        for score in scores:
            print(f"  DRY {score.trace_id[:12]} {score.name}={score.value!r}")
        print(f"dry run — {len(scores)} scores not sent")
        return 0

    from langfuse import get_client

    client = get_client()
    if not client.auth_check():
        print(
            "Langfuse rejected the credentials — check LANGFUSE_PUBLIC_KEY / "
            "LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL in .env",
            file=sys.stderr,
        )
        return 2

    for score in scores:
        client.create_score(
            name=score.name,
            value=score.value,
            trace_id=score.trace_id,
            score_id=score.score_id,
            data_type=score.data_type,
            comment=score.comment,
            metadata={"source": score.source},
        )
    client.flush()
    print(f"posted {len(scores)} scores")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="A graded .xlsx coding workbook, or a .jsonl trace file.",
    )
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help="Skip the workbook's human columns; post only the offline checks.",
    )
    parser.add_argument(
        "--human-only",
        action="store_true",
        help="Skip the offline checks; post only the human grades.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be posted and send nothing.",
    )
    args = parser.parse_args(argv)

    path: Path = args.path
    if not path.is_file():
        print(f"No such file: {path}", file=sys.stderr)
        return 2

    scores: list[Score] = []

    if path.suffix == ".jsonl":
        if args.human_only:
            print("--human-only needs a workbook, not a trace file", file=sys.stderr)
            return 2
        scores += automated_scores(path)
    elif path.suffix == ".xlsx":
        if not args.auto_only:
            human = workbook_scores(path)
            if not human:
                print(
                    "No grades found in the workbook's yellow columns — nothing to "
                    "port. Grade it and save before running this.",
                    file=sys.stderr,
                )
            scores += human
        if not args.human_only:
            trace_file = _matching_trace_file(path)
            if trace_file is None:
                print(f"note: no trace JSONL found for {path.stem}; skipping offline checks")
            else:
                scores += automated_scores(trace_file)
    else:
        print(f"Expected .xlsx or .jsonl, got {path.suffix}", file=sys.stderr)
        return 2

    by_name: dict[str, int] = {}
    for score in scores:
        by_name[score.name] = by_name.get(score.name, 0) + 1
    for name, count in sorted(by_name.items()):
        print(f"  {name}: {count}")

    return post(scores, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
