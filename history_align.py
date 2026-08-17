"""Span → ledger-id alignment. Pure function; not wired into /draft/history.

A mis-mapped span is worse than a missing one. Matching is content-only
(value / value_text tokens). Visible `f_…` ids in the prose are ignored as
evidence of support — they are the leak this pass exists to replace.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence

from schemas import DraftStatement, Fact, Ledger

# Trailing / inline id artifacts the drafting model currently leaks. Used only
# to keep matching from treating those tokens as content.
_ID_ARTIFACT = re.compile(
    r"\(\s*(?:fact_ids?:\s*)?(?:`?f_[A-Za-z0-9_]+`?(?:\s*,\s*)?)+\s*\)",
    re.IGNORECASE,
)
_BARE_LEDGER_ID = re.compile(r"\bf_[A-Za-z0-9_]+\b")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“])")
_TOKEN = re.compile(r"[a-z]+|\d+(?:\.\d+)?%?", re.IGNORECASE)
_LABEL = re.compile(r"\*\*(.+?):\*\*\s*")

_STOP = {
    "a",
    "about",
    "according",
    "additionally",
    "after",
    "age",
    "all",
    "also",
    "an",
    "and",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "by",
    "child",
    "currently",
    "during",
    "for",
    "from",
    "had",
    "has",
    "have",
    "her",
    "him",
    "his",
    "history",
    "however",
    "in",
    "including",
    "indicated",
    "into",
    "is",
    "it",
    "its",
    "noted",
    "of",
    "on",
    "or",
    "reported",
    "she",
    "student",
    "than",
    "that",
    "the",
    "their",
    "there",
    "these",
    "this",
    "to",
    "was",
    "were",
    "when",
    "which",
    "with",
}


def strip_id_artifacts(text: str) -> str:
    """Remove leaked ledger-id trailers/inlines so matching is content-only."""

    cleaned = _ID_ARTIFACT.sub("", text)
    cleaned = _BARE_LEDGER_ID.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def split_labeled_blocks(prose: str) -> list[tuple[str, str]]:
    """Split `**Label:** body` consumer prose into (label, body) pairs."""

    matches = list(_LABEL.finditer(prose))
    out: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prose)
        out.append((match.group(1), prose[start:end].strip()))
    return out


def split_sentences(prose: str) -> list[str]:
    text = (prose or "").strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _stem(token: str) -> str:
    t = token.lower()
    if t.endswith("%"):
        return t
    if t.isdigit() or re.fullmatch(r"\d+(?:\.\d+)?", t):
        return t
    for suffix in ("ing", "ed", "es", "s"):
        if len(t) > len(suffix) + 3 and t.endswith(suffix):
            return t[: -len(suffix)]
    return t


def _stems(text: str, extra_stop: set[str] | None = None) -> set[str]:
    stop = _STOP if extra_stop is None else _STOP | extra_stop
    out: set[str] = set()
    for raw in _TOKEN.findall(text or ""):
        token = raw.lower()
        if token in stop:
            continue
        if token.isdigit() or token.endswith("%"):
            out.add(token)
            continue
        if len(token) < 4:
            continue
        stemmed = _stem(token)
        if stemmed in stop or len(stemmed) < 3:
            continue
        out.add(stemmed)
    return out


def _name_stop(name: str | None) -> set[str]:
    if not name:
        return set()
    return {_stem(t) for t in _TOKEN.findall(name.lower()) if len(t) >= 3}


def _frequent_stems(facts: Sequence[Fact], extra_stop: set[str]) -> set[str]:
    if len(facts) < 3:
        return set()
    df: Counter[str] = Counter()
    for fact in facts:
        stems = _stems(fact.value or "", extra_stop) | _stems(fact.value_text or "", extra_stop)
        for token in stems:
            df[token] += 1
    threshold = max(3, int(len(facts) * 0.5 + 0.999))
    return {token for token, count in df.items() if count >= threshold}


def _is_content_number(token: str) -> bool:
    """Percents and multi-digit non-year numbers; not calendar days or 1/2."""

    if token.endswith("%"):
        return True
    if not token.isdigit() or len(token) < 2:
        return False
    value = int(token)
    return not (1900 <= value <= 2100)


def _strong_substring(needle: str, haystack: str) -> bool:
    if len(needle) < 16:
        return False
    return needle in haystack


_GENERIC = {
    "accuracy",
    "area",
    "clinical",
    "clinically",
    "concern",
    "development",
    "developmental",
    "evaluation",
    "history",
    "least",
    "measur",
    "problem",
    "range",
    "record",
    "regard",
    "sampl",
    "scor",
    "score",
    "suspect",
    "teacher",
    "work",
}


def _distinctive(stems: set[str]) -> set[str]:
    return {t for t in stems if t not in _GENERIC and t not in _STOP}


def match_fact_to_span(
    fact: Fact,
    span: str,
    *,
    extra_stop: set[str] | None = None,
) -> bool:
    """True only when the span carries this fact's content, not its id.

    Token matching uses the compact `value` when it has enough distinctive
    stems, otherwise `value_text`. A bag-of-topics value therefore cannot
    attach to a sentence that only shares one of its topics.
    """

    stop = extra_stop or set()
    working = _normalize(strip_id_artifacts(span))
    if not working:
        return False
    value = _normalize(fact.value or "")
    value_text = _normalize(fact.value_text or "")
    if _strong_substring(value, working) or _strong_substring(value_text, working):
        return True

    value_stems = _distinctive(_stems(value, stop) - stop)
    text_stems = _distinctive(_stems(value_text, stop) - stop)
    fact_stems = value_stems if len(value_stems) >= 2 else text_stems
    if not fact_stems:
        return False
    span_stems = _distinctive(_stems(working, stop) - stop)
    overlap = fact_stems & span_stems
    if not overlap:
        return False
    numeric = {t for t in overlap if _is_content_number(t)}
    ratio = len(overlap) / len(fact_stems)
    non_numeric = overlap - {t for t in overlap if t.isdigit() or t.endswith("%")}
    if numeric and non_numeric:
        return True
    if len(overlap) >= 2 and ratio >= 0.4 and non_numeric:
        return True
    # Percent/number alone is allowed only when it is the whole claim.
    if numeric and not non_numeric and ratio >= 0.5 and len(fact_stems) <= 2:
        return True
    return False


def _overlap_stems(fact: Fact, span: str, extra_stop: set[str]) -> set[str]:
    working = _normalize(strip_id_artifacts(span))
    value_stems = _distinctive(_stems(fact.value or "", extra_stop) - extra_stop)
    text_stems = _distinctive(_stems(fact.value_text or "", extra_stop) - extra_stop)
    fact_stems = value_stems if len(value_stems) >= 2 else text_stems
    span_stems = _distinctive(_stems(working, extra_stop) - extra_stop)
    return fact_stems & span_stems


def _drop_shared_numeric_only(
    matched: list[Fact],
    span: str,
    extra_stop: set[str],
) -> list[Fact]:
    """Drop a hit whose only overlap is a number another hit also claims."""

    if len(matched) < 2:
        return matched
    overlaps = {fact.id: _overlap_stems(fact, span, extra_stop) for fact in matched}
    kept: list[Fact] = []
    for fact in matched:
        overlap = overlaps[fact.id]
        nums = {t for t in overlap if t.isdigit() or t.endswith("%")}
        non_num = overlap - nums
        if non_num:
            kept.append(fact)
            continue
        shared = False
        for other in matched:
            if other.id == fact.id:
                continue
            other_nums = {
                t for t in overlaps[other.id] if t.isdigit() or t.endswith("%")
            }
            if nums & other_nums:
                shared = True
                break
        if not shared:
            kept.append(fact)
    return kept


def align_prose_to_facts(
    prose: str,
    facts: Sequence[Fact],
    *,
    exclude_name: str | None = None,
) -> list[DraftStatement]:
    """Map prose spans onto supporting ledger facts. Precision over recall.

    Unmatched substantive sentences are omitted — a missing id is cheaper than
    a wrong one. `fact.id` is never used as a matching signal.
    """

    extra_stop = _name_stop(exclude_name)
    extra_stop |= _frequent_stems(facts, extra_stop)
    statements: list[DraftStatement] = []
    for sentence in split_sentences(prose):
        claim = strip_id_artifacts(sentence)
        if len(claim) < 24:
            continue
        matched = [
            fact
            for fact in facts
            if match_fact_to_span(fact, sentence, extra_stop=extra_stop)
        ]
        matched = _drop_shared_numeric_only(matched, sentence, extra_stop)
        if not matched:
            continue
        # Preserve first-seen order; de-dupe ids.
        seen: set[str] = set()
        fact_ids: list[str] = []
        for fact in matched:
            if fact.id not in seen:
                seen.add(fact.id)
                fact_ids.append(fact.id)
        statements.append(
            DraftStatement(
                quote=sentence.strip(),
                statement=claim,
                fact_ids=fact_ids,
            )
        )
    return statements


def align_labeled_prose(
    prose: str,
    facts_by_label: dict[str, Sequence[Fact]],
    *,
    exclude_name: str | None = None,
) -> list[DraftStatement]:
    """Align each `**Label:**` block against that block's candidate facts."""

    statements: list[DraftStatement] = []
    for label, body in split_labeled_blocks(prose):
        facts = facts_by_label.get(label) or ()
        if not facts or not body.strip():
            continue
        statements.extend(
            align_prose_to_facts(body, facts, exclude_name=exclude_name)
        )
    return statements


def facts_for_ids(ledger: Ledger, fact_ids: Sequence[str]) -> list[Fact]:
    by_id = {f.id: f for f in ledger.facts}
    return [by_id[fid] for fid in fact_ids if fid in by_id]


def substantive_sentence_count(prose: str) -> int:
    """Sentences long enough to be a claim, after stripping id artifacts."""

    n = 0
    for sentence in split_sentences(prose):
        claim = strip_id_artifacts(sentence)
        if len(claim) >= 24:
            n += 1
    return n
