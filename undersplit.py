"""Hard rule 2 as an executed check — flag, do not re-extract, do not drop.

Signal (topic-free):
  A source sentence (same source_id + sentence) contains a serial list of
  three or more items (`X, Y, and Z` or semicolon lists) whose item *shapes*
  are mixed (token / phrase / "a …" NP / dose), and exactly one ledger fact
  maps to that sentence.

Why this signal:
  Packing across claim domains shows up as a heterogeneous list in one span
  with no sibling facts. A homogeneous list (dose rows, three adjectives, a
  token inventory) is one list-valued claim, not under-splitting. That keeps
  medications consolidation from needing a named-predicate carve-out.

Flag vs split:
  Stamp Fact.needs_claim_split and return UndersplitFinding. The fact stays.
  Re-extracting the span would be another model call Stage 1 has not
  thresholded; dropping would delete evidence. Not a firmer prompt sentence.
"""

from __future__ import annotations

import re
from collections import defaultdict

from derived import is_derived_fact
from schemas import Fact, Ledger, UndersplitFinding

_AND_OR_TAIL_RE = re.compile(r",\s+(?:and|or)\s+", re.IGNORECASE)
_SEMI_LIST_RE = re.compile(r"(?P<body>(?:[^;]+;\s*){2,}[^;.]+)")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_DOSE_RE = re.compile(r"\d")
_DOSE_UNIT_RE = re.compile(r"\b(?:mg|mcg|ml|g|units?)\b", re.IGNORECASE)
_PREAMBLE_SEPS = (" of ", " including ", ": ")


def _sentences(text: str) -> list[str]:
    return [p.strip() for p in _SENTENCE_RE.split(text or "") if p.strip()]


def _span_for_fact(fact: Fact, source_content: str) -> str:
    vt = (fact.value_text or fact.value or "").strip()
    if not vt:
        return ""
    for sent in _sentences(source_content):
        if vt in sent or sent in vt:
            return sent
    return vt


def _word_count(text: str) -> int:
    return len(re.findall(r"[a-z0-9]+", text.lower()))


def _peel_preamble(first: str, other_counts: list[int]) -> str:
    """Drop clause-level lead-in so only the list item remains."""

    lower = first.lower()
    for sep in _PREAMBLE_SEPS:
        idx = lower.rfind(sep)
        if idx != -1:
            peeled = first[idx + len(sep) :].strip()
            if peeled:
                return peeled
    if not other_counts:
        return first
    median = sorted(other_counts)[len(other_counts) // 2]
    words = first.split()
    if len(words) > median + 1:
        keep = min(3, max(1, median))
        return " ".join(words[-keep:])
    return first


def _serial_items(text: str) -> list[str]:
    match = _AND_OR_TAIL_RE.search(text or "")
    if not match:
        return []
    last = re.split(r"[.!?]", text[match.end() :], maxsplit=1)[0].strip()
    left = [p.strip() for p in text[: match.start()].split(",") if p.strip()]
    if not left or not last:
        return []
    others = left[1:] + [last]
    first = _peel_preamble(left[0], [_word_count(p) for p in others])
    items = [first, *others]
    return [p for p in items if p]


def _semi_items(text: str) -> list[str]:
    match = _SEMI_LIST_RE.search(text or "")
    if not match:
        return []
    return [p.strip() for p in match.group("body").split(";") if p.strip()]


def _list_items(text: str) -> list[str]:
    items = _serial_items(text)
    if len(items) >= 3:
        return items
    items = _semi_items(text)
    if len(items) >= 3:
        return items
    return []


def _item_shape(item: str) -> str:
    if _DOSE_RE.search(item) and _DOSE_UNIT_RE.search(item):
        return "dose"
    words = re.findall(r"[a-z0-9]+", item.lower())
    if len(words) <= 1:
        return "token"
    if words and words[0] == "a":
        return "np_a"
    return "phrase"


def is_heterogeneous_serial_list(text: str) -> bool:
    """True when text carries a 3+ item serial/semicolon list of mixed shapes."""

    items = _list_items(text)
    if len(items) < 3:
        return False
    shapes = {_item_shape(item) for item in items}
    return len(shapes) >= 2


def detect_undersplit_facts(ledger: Ledger) -> list[UndersplitFinding]:
    content_by_id = {s.id: s.content or "" for s in ledger.sources}
    candidates: list[tuple[Fact, str]] = []
    by_span: dict[tuple[str, str], list[Fact]] = defaultdict(list)

    for fact in ledger.facts:
        if is_derived_fact(fact):
            continue
        span = _span_for_fact(fact, content_by_id.get(fact.source_id, ""))
        if not span:
            continue
        by_span[(fact.source_id, span)].append(fact)
        candidates.append((fact, span))

    findings: list[UndersplitFinding] = []
    flagged: set[str] = set()
    for fact, span in candidates:
        if fact.id in flagged:
            continue
        siblings = by_span[(fact.source_id, span)]
        if len(siblings) != 1:
            continue
        blob = f"{span} {fact.value_text or ''} {fact.value or ''}"
        if not is_heterogeneous_serial_list(blob):
            continue
        flagged.add(fact.id)
        findings.append(
            UndersplitFinding(
                fact_id=fact.id,
                source_id=fact.source_id,
                span=span,
                summary=(
                    "One source span produced a single fact packing a mixed "
                    f"serial list ({fact.predicate}). Flag for split review."
                ),
            )
        )
    return findings


def stamp_undersplit_flags(ledger: Ledger) -> tuple[Ledger, list[UndersplitFinding]]:
    """Stamp needs_claim_split on flagged facts. Facts stay on the ledger."""

    findings = detect_undersplit_facts(ledger)
    flagged_ids = {f.fact_id for f in findings}
    if not flagged_ids:
        return ledger, findings
    facts = [
        fact.model_copy(update={"needs_claim_split": True})
        if fact.id in flagged_ids
        else fact.model_copy(update={"needs_claim_split": False})
        for fact in ledger.facts
    ]
    return ledger.model_copy(update={"facts": facts}), findings
