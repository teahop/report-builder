"""Offline TRACE panel helpers — read stored traces, score referral prose.

Display-only. No model calls. Validator modules are imported read-only.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from referral_draft import (
    _AGE_DOB_PATTERNS,
    _CATEGORY_DISPLAY,
    _HEADING_PATTERNS,
    _PLACEHOLDER_PATTERNS,
    normalize_client_quote_words,
)

WEEK1 = Path(__file__).resolve().parents[1]
REFERRAL_TRACES_DIR = WEEK1 / "evals" / "referral" / "traces"
HISTORY_TRACES_DIR = WEEK1 / "evals" / "history" / "traces"
BASELINE_TRACES_DIR = WEEK1 / "evals" / "traces"
TAXONOMY_PATH = WEEK1 / "evals" / "taxonomy.json"
BASELINE_CODED_PATH = WEEK1 / "evals" / "history" / "baseline_coded.json"
REFERRAL_SMOKE_SCRIPT = WEEK1 / "evals" / "referral" / "run_smoke.py"
HISTORY_SMOKE_SCRIPT = WEEK1 / "evals" / "history" / "run_smoke.py"

BEFORE_STAMP = "181712"
AFTER_STAMP = "190139"
HISTORY_BASELINE_SESSION = "sweep-20260807-132534-c9e20e"
HISTORY_BASELINE_SAMPLE = (
    HISTORY_TRACES_DIR / "baseline_sample_sweep-20260807.jsonl"
)
HISTORY_BANNER = (
    "DIAGNOSTIC — unaccepted upstream parent (extraction not accepted)"
)

# Same client-quote span finder as validate_referral_draft.
_QUOTE_SPAN = re.compile(r'"([^"\n]{3,})"|“([^”\n]{3,})”')
# Exact leakage tokens from evals/referral/run_smoke.py (in addition to validator regexes).
_SMOKE_LEAKAGE_TOKENS = ("2014-09-12", "DOB", "year-old")

CHECK_PARAGRAPH_COUNT = "paragraph_count"
CHECK_LEAKAGE = "header_placeholder_leakage"
CHECK_CATEGORIES_LAST = "categories_last"
CHECK_QUOTE_POLICY = "quote_policy"
CHECK_DOB_AGE_OPENER = "no_dob_age_opener"
CHECK_SUMMARATIVE = "no_summarative_register"
REFERRAL_CHECK_NAMES = (
    CHECK_PARAGRAPH_COUNT,
    CHECK_LEAKAGE,
    CHECK_CATEGORIES_LAST,
    CHECK_QUOTE_POLICY,
)
HISTORY_CHECK_NAMES = (CHECK_DOB_AGE_OPENER, CHECK_SUMMARATIVE)

# TRACE fix-1 handoff: first sentence of the first block. Baseline coded 20/20 fail.
_DOB_AGE_OPENER = re.compile(
    r"(born\s+on|date\s+of\s+birth|\bDOB\b|"
    r"\b\d{1,2}\s+years?\s+old\b|"
    r"\b\d{1,2}-year-old\b|"
    r"\bcurrently\s+\d{1,2}\b)",
    re.IGNORECASE,
)
_BLOCK_LABEL_PREFIX = re.compile(r"^\*\*[^*]+\*\*:\s*")
# Observed baseline phrase hits (high precision, unknown recall — tripwire, not register quality).
SUMMARATIVE_PHRASES = (
    "despite these",
    "complex history",
    "overall,",
    "underscore",
    "highlight the",
    "notably",
    "essential to highlight",
    "in summary",
    "invites a deeper",
    "this contrast",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    n_pass: int | None = None
    n: int | None = None


@dataclass(frozen=True)
class LoadedTrace:
    path: Path
    kind: str  # "referral" | "history"
    records: list[dict]


def openai_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def list_trace_files() -> list[Path]:
    paths: list[Path] = []
    for folder in (BASELINE_TRACES_DIR, REFERRAL_TRACES_DIR, HISTORY_TRACES_DIR):
        if not folder.is_dir():
            continue
        paths.extend(sorted(folder.glob("*.jsonl")))
    return paths


def trace_kind(path: Path) -> str:
    parts = path.resolve().parts
    if "referral" in parts:
        return "referral"
    if "history" in parts:
        return "history"
    if path.resolve().parent == BASELINE_TRACES_DIR.resolve():
        return "history"
    return "unknown"


def load_trace_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    records: list[dict] = []
    try:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
        if records:
            return records
    except json.JSONDecodeError:
        pass
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Unsupported trace JSON in {path}")


def load_trace(path: Path) -> LoadedTrace:
    kind = trace_kind(path)
    return LoadedTrace(path=path, kind=kind, records=load_trace_file(path))


def find_trace_by_stamp(stamp: str, *, kind: str = "referral") -> Path | None:
    folder = REFERRAL_TRACES_DIR if kind == "referral" else HISTORY_TRACES_DIR
    matches = sorted(folder.glob(f"*{stamp}*.jsonl"))
    return matches[0] if matches else None


def trace_metadata(record: dict) -> dict:
    prompt_sha = (
        record.get("prompt_sha256")
        or record.get("prompt_hash")
        or record.get("prompt_sha")
        or record.get("writer_prompt_hash")
    )
    return {
        "fixture_id": record.get("fixture_id"),
        "model": record.get("model"),
        "temperature": record.get("temperature"),
        "prompt_sha256": prompt_sha,
        "voice_store_sha": record.get("voice_store_sha"),
        "tokens_used": record.get("tokens_used"),
        "cost_usd": record.get("cost_usd"),
        "latency_ms": record.get("latency_ms"),
        "status": record.get("status"),
        "paragraph_count": record.get("paragraph_count"),
    }


def display_prose(record: dict, *, kind: str) -> str:
    if kind == "history" and record.get("rendered_prose"):
        return str(record["rendered_prose"])
    if record.get("prose"):
        return str(record["prose"])
    if kind == "history":
        parts: list[str] = []
        for section in record.get("sections") or []:
            prose = (section.get("prose") or "").strip()
            if not prose:
                continue
            label = section.get("display_label") or section.get("section_key") or ""
            parts.append(f"{label}\n{prose}" if label else prose)
        return "\n\n".join(parts)
    error = record.get("error") or record.get("observed_failure")
    if error:
        return ""
    return ""


def load_taxonomy(path: Path | None = None) -> dict:
    target = path or TAXONOMY_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def _last_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    last_para = stripped.split("\n\n")[-1].strip()
    pieces = [p.strip() for p in re.split(r"(?<=[.!?])\s+", last_para) if p.strip()]
    return pieces[-1] if pieces else last_para


def _has_category_label(text: str) -> bool:
    for display in _CATEGORY_DISPLAY.values():
        if re.search(rf"\b{re.escape(display)}\b", text, re.IGNORECASE):
            return True
    return False


def _paragraph_count(record: dict) -> int:
    if "paragraph_count" in record and record["paragraph_count"] is not None:
        try:
            return int(record["paragraph_count"])
        except (TypeError, ValueError):
            return 0
    paragraphs = record.get("paragraphs") or []
    return len(paragraphs)


def check_paragraph_count(record: dict) -> CheckResult:
    count = _paragraph_count(record)
    return CheckResult(
        name=CHECK_PARAGRAPH_COUNT,
        passed=count == 1,
        detail=f"paragraph_count={count} (expected 1)",
    )


def check_header_placeholder_leakage(prose: str) -> CheckResult:
    if not prose.strip():
        return CheckResult(
            name=CHECK_LEAKAGE,
            passed=False,
            detail="no prose to inspect",
        )
    hits: list[str] = []
    for pattern in (*_PLACEHOLDER_PATTERNS, *_AGE_DOB_PATTERNS, *_HEADING_PATTERNS):
        if pattern.search(prose):
            hits.append(pattern.pattern)
    lowered = prose.lower()
    for token in _SMOKE_LEAKAGE_TOKENS:
        if token.lower() in lowered and token not in hits:
            hits.append(token)
    return CheckResult(
        name=CHECK_LEAKAGE,
        passed=not hits,
        detail="clear" if not hits else "matched: " + "; ".join(hits),
    )


def check_categories_last(prose: str) -> CheckResult:
    if not prose.strip():
        return CheckResult(
            name=CHECK_CATEGORIES_LAST,
            passed=False,
            detail="no prose to inspect",
        )
    last = _last_sentence(prose)
    passed = _has_category_label(last)
    return CheckResult(
        name=CHECK_CATEGORIES_LAST,
        passed=passed,
        detail=(
            "category label in final sentence"
            if passed
            else f"final sentence has no category label: {last!r}"
        ),
    )


def check_quote_policy(
    prose: str,
    verbatim_quote_raw_texts: list[str] | None = None,
) -> CheckResult:
    if not prose.strip():
        return CheckResult(
            name=CHECK_QUOTE_POLICY,
            passed=False,
            detail="no prose to inspect",
        )
    authorized = {
        normalize_client_quote_words(text)
        for text in (verbatim_quote_raw_texts or [])
        if text and text.strip()
    }
    unauthorized: list[str] = []
    for match in _QUOTE_SPAN.finditer(prose):
        quoted = match.group(1) or match.group(2) or ""
        if normalize_client_quote_words(quoted) not in authorized:
            unauthorized.append(quoted)
    return CheckResult(
        name=CHECK_QUOTE_POLICY,
        passed=not unauthorized,
        detail=(
            "no unauthorized quoted spans"
            if not unauthorized
            else "unauthorized quotes: " + "; ".join(repr(q) for q in unauthorized)
        ),
    )


def score_referral_record(record: dict) -> list[CheckResult]:
    kind_prose = display_prose(record, kind="referral")
    verbatim = record.get("verbatim_quote_raw_texts") or []
    if not isinstance(verbatim, list):
        verbatim = []
    return [
        check_paragraph_count(record),
        check_header_placeholder_leakage(kind_prose),
        check_categories_last(kind_prose),
        check_quote_policy(kind_prose, verbatim),
    ]


def all_checks_passed(results: list[CheckResult]) -> bool:
    return bool(results) and all(item.passed for item in results)


def check_delta(before: CheckResult, after: CheckResult) -> str:
    if before.name != after.name:
        raise ValueError(f"check name mismatch: {before.name} vs {after.name}")
    if not before.passed and after.passed:
        return "fail → pass"
    if before.passed and not after.passed:
        return "pass → fail"
    if before.passed:
        return "unchanged pass"
    return "unchanged fail"


def before_after_deltas(
    before_results: list[CheckResult],
    after_results: list[CheckResult],
) -> list[dict]:
    after_by_name = {item.name: item for item in after_results}
    rows: list[dict] = []
    for before in before_results:
        after = after_by_name[before.name]
        rows.append(
            {
                "check": before.name,
                "before": "pass" if before.passed else "fail",
                "after": "pass" if after.passed else "fail",
                "delta": check_delta(before, after),
                "before_detail": before.detail,
                "after_detail": after.detail,
            }
        )
    return rows


def _first_content_paragraph(text: str) -> str:
    for para in text.split("\n\n"):
        line = para.strip()
        if not line or line.startswith("#"):
            continue
        line = _BLOCK_LABEL_PREFIX.sub("", line).strip()
        if line:
            return line
    return ""


def first_block_first_sentence(record: dict) -> str:
    text = ""
    blocks = record.get("blocks") or []
    if blocks and isinstance(blocks[0], dict) and (blocks[0].get("prose") or "").strip():
        text = str(blocks[0]["prose"])
    else:
        sections = record.get("sections") or []
        if sections and (sections[0].get("prose") or "").strip():
            text = str(sections[0]["prose"])
        else:
            text = display_prose(record, kind="history")
    paragraph = _first_content_paragraph(text)
    if not paragraph:
        return ""
    pieces = [p.strip() for p in re.split(r"(?<=[.!?])\s+", paragraph) if p.strip()]
    return pieces[0] if pieces else paragraph


def check_no_dob_age_opener(record: dict) -> CheckResult:
    sentence = first_block_first_sentence(record)
    if not sentence:
        return CheckResult(
            name=CHECK_DOB_AGE_OPENER,
            passed=False,
            detail="no first-block sentence to inspect",
        )
    hit = _DOB_AGE_OPENER.search(sentence)
    return CheckResult(
        name=CHECK_DOB_AGE_OPENER,
        passed=hit is None,
        detail=(
            "first block does not open with DOB/age"
            if hit is None
            else f"opener recites DOB/age: {sentence!r}"
        ),
    )


def check_no_summarative_register(record: dict) -> CheckResult:
    prose = display_prose(record, kind="history")
    if not prose.strip():
        return CheckResult(
            name=CHECK_SUMMARATIVE,
            passed=False,
            detail="no prose to inspect",
        )
    lowered = prose.lower()
    hits = [phrase for phrase in SUMMARATIVE_PHRASES if phrase in lowered]
    return CheckResult(
        name=CHECK_SUMMARATIVE,
        passed=not hits,
        detail=(
            "no observed summarative phrases"
            if not hits
            else "matched: " + ", ".join(hits)
        ),
    )


def score_history_record(record: dict) -> list[CheckResult]:
    return [
        check_no_dob_age_opener(record),
        check_no_summarative_register(record),
    ]


def aggregate_check_results(records: list[dict]) -> list[CheckResult]:
    if not records:
        return [
            CheckResult(CHECK_DOB_AGE_OPENER, False, "no records"),
            CheckResult(CHECK_SUMMARATIVE, False, "no records"),
        ]
    scored = [score_history_record(record) for record in records]
    aggregated: list[CheckResult] = []
    for name in HISTORY_CHECK_NAMES:
        n = len(scored)
        n_pass = sum(
            1
            for row in scored
            if next(item.passed for item in row if item.name == name)
        )
        aggregated.append(
            CheckResult(
                name=name,
                passed=n_pass == n,
                detail=f"{n_pass}/{n} pass",
                n_pass=n_pass,
                n=n,
            )
        )
    return aggregated


def load_baseline_coded(path: Path | None = None) -> dict:
    target = path or BASELINE_CODED_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def coded_baseline_results() -> list[CheckResult]:
    data = load_baseline_coded()
    opener = data["checks"][CHECK_DOB_AGE_OPENER]
    n = int(opener["n"])
    n_pass = int(opener["pass"])
    return [
        CheckResult(
            name=CHECK_DOB_AGE_OPENER,
            passed=n_pass == n,
            detail=f"coded {n_pass}/{n} pass (Langfuse {data.get('source', '')})",
            n_pass=n_pass,
            n=n,
        ),
        CheckResult(
            name=CHECK_SUMMARATIVE,
            passed=False,
            detail=(
                "coded in the same open-coding category; "
                "phrase hits live in taxonomy.json"
            ),
            n=n,
        ),
    ]


def history_baseline_sample() -> dict | None:
    """One 8/7 draft for the Before column. Does not replace the coded n=20 counts."""

    if not HISTORY_BASELINE_SAMPLE.is_file():
        return None
    records = load_trace_file(HISTORY_BASELINE_SAMPLE)
    return records[0] if records else None


def history_baseline_jsonl() -> Path | None:
    """Only the 8/7 coded baseline session — never a later sweep in the same folder."""

    if not BASELINE_TRACES_DIR.is_dir():
        return None
    preferred = sorted(BASELINE_TRACES_DIR.glob(f"*{HISTORY_BASELINE_SESSION}*.jsonl"))
    return preferred[0] if preferred else None


def newest_history_smoke() -> Path | None:
    matches = sorted(HISTORY_TRACES_DIR.glob("*.jsonl"))
    return matches[-1] if matches else None


def history_after_jsonl() -> Path | None:
    """Newest History writer sweep in evals/traces/, excluding the 8/7 baseline."""

    if BASELINE_TRACES_DIR.is_dir():
        sweeps = sorted(
            path
            for path in BASELINE_TRACES_DIR.glob("sweep-*.jsonl")
            if HISTORY_BASELINE_SESSION not in path.name
        )
        if sweeps:
            return sweeps[-1]
    return newest_history_smoke()


@dataclass(frozen=True)
class HistoryComparison:
    before_label: str
    after_label: str
    before_source: str
    after_path: Path | None
    before_results: list[CheckResult]
    after_results: list[CheckResult]
    after_record: dict | None
    before_record: dict | None = None

    @property
    def deltas(self) -> list[dict]:
        return before_after_deltas(self.before_results, self.after_results)


def history_before_after() -> HistoryComparison:
    after_path = history_after_jsonl()
    after_record = None
    after_results: list[CheckResult] = [
        CheckResult(CHECK_DOB_AGE_OPENER, False, "no history after-set on disk"),
        CheckResult(CHECK_SUMMARATIVE, False, "no history after-set on disk"),
    ]
    after_label = "(no history after-set)"
    if after_path is not None:
        loaded = load_trace(after_path)
        after_record = loaded.records[0] if loaded.records else None
        if loaded.records:
            after_results = (
                aggregate_check_results(loaded.records)
                if len(loaded.records) > 1
                else score_history_record(loaded.records[0])
            )
        after_label = f"{after_path.name} (n={len(loaded.records)})"

    baseline_path = history_baseline_jsonl()
    before_record = None
    if baseline_path is not None:
        loaded = load_trace(baseline_path)
        before_results = aggregate_check_results(loaded.records)
        before_label = f"{baseline_path.name} (n={len(loaded.records)})"
        before_source = "jsonl"
        before_record = loaded.records[0] if loaded.records else None
    else:
        before_results = coded_baseline_results()
        before_label = f"coded baseline {HISTORY_BASELINE_SESSION} (n=20, jsonl not on disk)"
        before_source = "coded"
        before_record = history_baseline_sample()

    return HistoryComparison(
        before_label=before_label,
        after_label=after_label,
        before_source=before_source,
        after_path=after_path,
        before_results=before_results,
        after_results=after_results,
        after_record=after_record,
        before_record=before_record,
    )
