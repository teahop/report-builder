"""Block-granularity temporal anchoring and the C1 anchor-drift check.

A document often carries a contiguous passage whose reference date is not the
print/source date: a copied prior record under a date-led heading, a reporting
period dashboard with its own start date, a year-span header. Facts from that
passage inherit the region's date as ``as_of_date``. No clinical topic is named.

C1 (staleness spec §6): a fact whose claim text or containing block carries an
explicit date older than ``source_date`` while ``as_of_date`` still equals
``source_date``. Calibrate against doc_11 before trusting it elsewhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from schemas import AnchorDriftFinding, ExtractedFactDraft, Fact, Ledger, Source

_ISO_RE = re.compile(r"\b((?:19|20)\d{2}-\d{2}-\d{2})\b")
_US_LONG_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/((?:19|20)\d{2})\b")
_US_SHORT_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2})\b")
_YEAR_SPAN_RE = re.compile(r"\b((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2})\b")
_YEAR_LED_RE = re.compile(r"^\s*((?:19|20)\d{2})\s*:")
_START_DATE_RE = re.compile(r"\bStart\s*Date\s*:\s*", re.IGNORECASE)
_DATE_LED_RE = re.compile(
    r"^\s*(?:"
    r"(?:19|20)\d{2}-\d{2}-\d{2}"
    r"|\d{1,2}/\d{1,2}/(?:\d{2}|(?:19|20)\d{2})"
    r")"
)

# Long narrative sentences are not region openers even if they mention a date.
_MAX_OPENER_LEN = 240


@dataclass(frozen=True, slots=True)
class DatedBlock:
    """One contiguous region whose claims inherit ``as_of``."""

    start: int
    end: int
    as_of: str
    heading: str


def _expand_two_digit_year(year: int) -> int:
    return 2000 + year if year <= 29 else 1900 + year


def _ymd(year: int, month: int, day: int) -> str | None:
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    if not (1900 <= year <= 2100):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_explicit_dates(text: str) -> list[str]:
    """ISO dates from ISO, US numeric, and two-digit-year forms. No relative time."""

    found: list[str] = []
    seen: set[str] = set()

    def _add(iso: str | None) -> None:
        if iso and iso not in seen:
            seen.add(iso)
            found.append(iso)

    for match in _ISO_RE.finditer(text or ""):
        _add(match.group(1))
    for match in _US_LONG_RE.finditer(text or ""):
        _add(_ymd(int(match.group(3)), int(match.group(1)), int(match.group(2))))
    for match in _US_SHORT_RE.finditer(text or ""):
        # Do not re-parse a four-digit year already captured by _US_LONG_RE.
        span = match.group(0)
        if len(match.group(3)) == 2 and not re.search(r"/\d{4}\b", span):
            _add(
                _ymd(
                    _expand_two_digit_year(int(match.group(3))),
                    int(match.group(1)),
                    int(match.group(2)),
                )
            )
    return found


def _oldest_older_than(dates: list[str], source_date: str) -> str | None:
    older = [d for d in dates if d < source_date]
    if not older:
        return None
    return min(older)


def _line_offsets(content: str) -> list[tuple[int, int, str]]:
    lines: list[tuple[int, int, str]] = []
    start = 0
    for line in (content or "").splitlines(keepends=True):
        end = start + len(line)
        lines.append((start, end, line.rstrip("\r\n")))
        start = end
    return lines


def _running_header_dates(content: str, source_date: str) -> frozenset[str]:
    """Dates that repeat as document chrome (the print/source date itself)."""

    counts: dict[str, int] = {}
    for _, _, line in _line_offsets(content):
        if len(line.strip()) > _MAX_OPENER_LEN:
            continue
        for iso in parse_explicit_dates(line):
            counts[iso] = counts.get(iso, 0) + 1
    running = {iso for iso, n in counts.items() if n >= 3 and iso == source_date}
    running.add(source_date)
    return frozenset(running)


def _opener_date(line: str, source_date: str, running: frozenset[str]) -> str | None:
    stripped = (line or "").strip()
    if not stripped or len(stripped) > _MAX_OPENER_LEN:
        return None

    start_m = _START_DATE_RE.search(stripped)
    if start_m:
        tail = stripped[start_m.end() :]
        dates = parse_explicit_dates(tail) or parse_explicit_dates(stripped)
        if dates and dates[0] not in running and dates[0] != source_date:
            return dates[0]
        return None

    year_led = _YEAR_LED_RE.match(stripped)
    if year_led:
        year = year_led.group(1)
        if year < source_date[:4]:
            return f"{year}-01-01"
        return None

    if _DATE_LED_RE.match(stripped):
        dates = parse_explicit_dates(stripped)
        if dates and dates[0] not in running and dates[0] != source_date:
            return dates[0]
        return None

    span = _YEAR_SPAN_RE.search(stripped)
    if span:
        y1, y2 = span.group(1), span.group(2)
        iso = f"{y1}-01-01"
        if y1 < y2 and iso != source_date:
            # Span on a header line — start-year 01-01 matches the year-only convention.
            rest = stripped[: span.start()] + stripped[span.end() :]
            compact = re.sub(r"\s+", " ", rest).strip()
            if len(stripped) <= 240 and len(compact) < 80:
                return iso
    return None


def _extend_start_to_heading(content: str, opener_start: int) -> int:
    """Include the short heading line above a Start Date field."""

    if opener_start <= 0:
        return opener_start
    before = content[:opener_start].rstrip("\r\n")
    nl = before.rfind("\n")
    prev = before[nl + 1 :] if nl >= 0 else before
    if not prev.strip():
        # skip one blank line
        before = before[:nl].rstrip("\r\n") if nl >= 0 else ""
        nl = before.rfind("\n")
        prev = before[nl + 1 :] if nl >= 0 else before
        opener_start = (nl + 1) if nl >= 0 else 0
    if prev.strip() and len(prev.strip()) <= _MAX_OPENER_LEN and not _DATE_LED_RE.match(prev):
        return (nl + 1) if nl >= 0 else 0
    return opener_start


def detect_dated_blocks(content: str, source_date: str) -> tuple[DatedBlock, ...]:
    """
    Regions opened by a date-led line, a Start Date field, or a year-span header.

    Running copies of ``source_date`` are not openers. Relative time is ignored.
    """

    text = content or ""
    if not text:
        return ()
    running = _running_header_dates(text, source_date)
    openers: list[tuple[int, str, str, bool]] = []
    for start, _end, line in _line_offsets(text):
        as_of = _opener_date(line, source_date, running)
        if as_of is None:
            continue
        is_start_date = bool(_START_DATE_RE.search(line))
        region_start = _extend_start_to_heading(text, start) if is_start_date else start
        openers.append((region_start, as_of, line.strip()[:120], is_start_date))

    if not openers:
        return ()

    openers.sort(key=lambda row: row[0])
    blocks: list[DatedBlock] = []
    for i, (start, as_of, heading, _) in enumerate(openers):
        end = openers[i + 1][0] if i + 1 < len(openers) else len(text)
        if end <= start:
            continue
        blocks.append(DatedBlock(start=start, end=end, as_of=as_of, heading=heading))
    return tuple(blocks)


def locate_claim(value_text: str, content: str) -> int | None:
    """Character offset of the claim in source text, or None if not found."""

    hay = content or ""
    needle = (value_text or "").strip()
    if not hay or not needle:
        return None
    idx = hay.find(needle)
    if idx >= 0:
        return idx
    # Prefer the longest leading slice that still matches.
    for length in range(min(len(needle), 80), 23, -1):
        piece = needle[:length].rstrip(" ,;.")
        if len(piece) < 24:
            break
        idx = hay.find(piece)
        if idx >= 0:
            return idx
    return None


def block_containing(offset: int | None, blocks: tuple[DatedBlock, ...]) -> DatedBlock | None:
    if offset is None:
        return None
    for block in blocks:
        if block.start <= offset < block.end:
            return block
    return None


def inherit_block_as_of(
    draft: ExtractedFactDraft,
    source: Source,
    blocks: tuple[DatedBlock, ...] | None = None,
) -> str | None:
    """Block date when the claim sits in a dated region; else None."""

    if blocks is None:
        blocks = detect_dated_blocks(source.content or "", source.date)
    offset = locate_claim(draft.value_text or "", source.content or "")
    if offset is None:
        offset = locate_claim(draft.value or "", source.content or "")
    block = block_containing(offset, blocks)
    if block is None:
        return None
    if block.as_of == source.date:
        return None
    return block.as_of


def claim_local_as_of(draft: ExtractedFactDraft, source_date: str) -> str | None:
    """Oldest explicit date in the claim wording that is older than source_date."""

    blob = f"{draft.value_text or ''} {draft.value or ''}"
    return _oldest_older_than(parse_explicit_dates(blob), source_date)


def resolve_as_of_date(
    draft: ExtractedFactDraft,
    source: Source,
    blocks: tuple[DatedBlock, ...] | None = None,
) -> str:
    """
    Precedence: claim-local date, then containing block, then a model proposal
    supported by the source text, else ``source.date``.
    """

    if blocks is None:
        blocks = detect_dated_blocks(source.content or "", source.date)

    local = claim_local_as_of(draft, source.date)
    if local:
        return local

    inherited = inherit_block_as_of(draft, source, blocks)
    if inherited:
        return inherited

    proposed = (draft.as_of_date or "").strip() or source.date
    if proposed == source.date:
        return source.date

    blob = f"{draft.value_text or ''} {draft.value or ''} {source.content or ''}"
    if proposed in blob:
        return proposed
    year = proposed[:4]
    if year.isdigit() and re.search(rf"\b{year}\b", blob):
        return proposed
    return source.date


def check_anchor_drift(ledger: Ledger) -> list[AnchorDriftFinding]:
    """
    C1: claim or containing block has an older explicit date, but as_of still
    equals source_date. Derived/request facts are skipped.
    """

    by_id = {s.id: s for s in ledger.sources}
    findings: list[AnchorDriftFinding] = []
    blocks_by_source: dict[str, tuple[DatedBlock, ...]] = {}

    for fact in ledger.facts:
        if fact.derivation or fact.source_id in {"computed", "request"}:
            continue
        source = by_id.get(fact.source_id)
        if source is None:
            continue
        as_of = fact.as_of_date or fact.source_date
        if as_of != fact.source_date:
            continue

        blob = f"{fact.value_text or ''} {fact.value or ''}"
        local = _oldest_older_than(parse_explicit_dates(blob), fact.source_date)
        if source.id not in blocks_by_source:
            blocks_by_source[source.id] = detect_dated_blocks(
                source.content or "", source.date
            )
        offset = locate_claim(fact.value_text or "", source.content or "")
        block = block_containing(offset, blocks_by_source[source.id])
        block_date = block.as_of if block is not None else None
        older = local or (
            block_date if block_date and block_date < fact.source_date else None
        )
        if older is None:
            continue
        findings.append(
            AnchorDriftFinding(
                fact_id=fact.id,
                source_id=fact.source_id,
                source_date=fact.source_date,
                as_of_date=as_of,
                block_date=older,
                summary=(
                    f"{fact.id} as_of_date still equals source_date "
                    f"{fact.source_date}; containing region/claim dates {older}"
                ),
            )
        )
    return findings
