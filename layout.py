"""Document-structure occupancy — a layout string is not a claim.

Banner lines, running titles, form labels, and partial projections of a
columnar name row occupy document structure. A validator that named a
predicate here would be a bug (spec §9). Relative time and clinical
topics are out of scope.
"""

from __future__ import annotations

import re

from schemas import ExtractedFactDraft, Source

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

# Form/column chrome — not claim language.
_LABEL_TOKENS = frozenset(
    {
        "last",
        "first",
        "middle",
        "name",
        "names",
        "suffix",
        "stuid",
        "id",
        "gender",
        "grade",
        "student",
        "client",
        "individual",
        "evaluated",
        "report",
        "dob",
        "birth",
        "date",
        "of",
        "the",
        "being",
    }
)

_NAME_PART_LABELS = frozenset({"last", "first", "middle"})


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def _nonempty_lines(content: str) -> list[str]:
    return [ln.strip() for ln in (content or "").splitlines() if ln.strip()]


def _is_label_echo(value_tokens: list[str]) -> bool:
    if not value_tokens:
        return False
    return set(value_tokens) <= _LABEL_TOKENS


def _is_banner_fragment(value_tokens: list[str], lines: list[str]) -> bool:
    """
    True when the value is a proper subset of an early title line.

    A two-token line that is only a name is a field fill, not a banner.
    A longer title that happens to contain a last-name token is chrome.
    """

    if not value_tokens or len(value_tokens) > 2:
        return False
    if any(t.isdigit() for t in value_tokens):
        return False
    for line in lines[:8]:
        line_tokens = _tokens(line)
        if len(line_tokens) < 4:
            continue
        if line_tokens[0].isdigit():
            continue
        if set(value_tokens) < set(line_tokens):
            return True
    return False


def _parse_columnar_name_parts(content: str) -> tuple[str, str, str] | None:
    """
    Last / First / Middle cells from a header+data identity row.

    Returns (last, first, middle) when a header names at least last+first+middle
    and the next data line supplies those cells. Missing middle is "".
    """

    lines = _nonempty_lines(content)
    for i, line in enumerate(lines[:-1]):
        labels = _tokens(line)
        if not _NAME_PART_LABELS <= set(labels):
            continue
        # Preserve label order so cells align.
        positions: dict[str, int] = {}
        for idx, tok in enumerate(labels):
            if tok in _NAME_PART_LABELS and tok not in positions:
                positions[tok] = idx
        if "last" not in positions or "first" not in positions:
            continue
        data = lines[i + 1]
        # Split on 2+ spaces / tabs, the usual flattened-table remnant.
        cells = [c.strip() for c in re.split(r"[ \t]{2,}", data) if c.strip()]
        if len(cells) < 2:
            cells = data.split()
        # Header tokens include chrome (stuid, gender, …). Map name-part
        # indexes relative to the label sequence, then onto cells by order of
        # name-part labels among all header tokens — too brittle.
        # Instead: drop leading id-like first cell, take remaining as
        # last, first, middle in header order.
        ordered = sorted(positions.items(), key=lambda kv: kv[1])
        # Count header tokens before the first name-part label — those are
        # leading chrome cells (StuID).
        first_name_idx = min(positions.values())
        leading = first_name_idx
        body = cells[leading:] if leading < len(cells) else cells
        by_part = {"last": "", "first": "", "middle": ""}
        for part, _pos in ordered:
            # Each name part consumes one cell; middle may be two given names
            # in one cell ("Andres Rafael").
            if not body:
                break
            by_part[part] = body.pop(0)
        if by_part["last"] and by_part["first"]:
            return by_part["last"], by_part["first"], by_part["middle"]
    return None


def _is_partial_name_projection(value_tokens: list[str], parts: tuple[str, str, str]) -> bool:
    last_t, first_t, middle_t = (_tokens(parts[0]), _tokens(parts[1]), _tokens(parts[2]))
    val = set(value_tokens)
    if not val:
        return False
    last_s, first_s, middle_s = set(last_t), set(first_t), set(middle_t)
    full = first_s | middle_s | last_s
    if not val <= full:
        return False
    # Complete ordinary name (first+last, optionally with middle) is a claim.
    if first_s and first_s <= val and last_s <= val:
        return False
    # Last only, middle only, or middle+last (first omitted) is column occupancy.
    if val == last_s:
        return True
    if middle_s and val == middle_s:
        return True
    if middle_s and val == (middle_s | last_s):
        return True
    if val == first_s:
        return True
    return False


def identity_first_last(content: str) -> tuple[str, str] | None:
    """First + last cells from a Last/First/Middle identity row, if present."""

    parts = _parse_columnar_name_parts(content)
    if parts is None:
        return None
    last, first, _middle = parts
    if last and first:
        return first, last
    return None


def name_field_fill(content: str) -> str | None:
    """First non-label, non-date fill after a name-field heading, if any."""

    lines = _nonempty_lines(content)
    for i, line in enumerate(lines):
        if not re.search(
            r"(name of individual|student(?:'s)?\s+name|name of student|client name)",
            line,
            re.IGNORECASE,
        ):
            continue
        for nxt in lines[i + 1 : i + 8]:
            toks = _tokens(nxt)
            if not toks or _is_label_echo(toks):
                continue
            if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", nxt.strip()):
                continue
            if 1 <= len(toks) <= 4:
                return nxt.strip()
            break
    return None


def is_document_structure_value(draft: ExtractedFactDraft, source: Source) -> bool:
    """
    True when the draft value occupies banner, label, or name-column structure
    rather than stating a claim. Predicate-blind by construction.
    """

    value_tokens = _tokens(draft.value or "")
    if not value_tokens:
        return False
    if _is_label_echo(value_tokens):
        return True
    lines = _nonempty_lines(source.content or "")
    if _is_banner_fragment(value_tokens, lines):
        return True
    parts = _parse_columnar_name_parts(source.content or "")
    if parts is not None and _is_partial_name_projection(value_tokens, parts):
        return True
    return False
