"""Deterministic History evidence gates — domain checks, preflight, episodes.

Shared by extraction skip filters, selectors, and the Layer-3 compiler so
plausible-wrong ledger rows cannot silently assemble into a drafting brief.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from schemas import Fact, Ledger, Source

# --- Domain / speech-act patterns (structural, not case-specific strings) ---

DEVELOPMENTAL_DOMAIN_RE = re.compile(
    r"\b("
    r"typical|atypical|delayed|delays?|milestone|pregnan|neonatal|prenatal|"
    r"birth|labor|delivery|nicu|walk(?:ed|ing)?|talk(?:ed|ing)?|toilet|"
    r"crawl(?:ed|ing)?|sat\b|sitting|stood|standing|first\s+words?|"
    r"two[- ]word|speech\s+develop|language\s+develop|motor\s+develop|"
    r"cognitive\s+develop|infant|toddler|early\s+develop|"
    r"develop(?:mental)?\s+(?:course|progress|milestones?)"
    r")\b",
    re.IGNORECASE,
)

TRAUMA_NARRATIVE_RE = re.compile(
    r"\b("
    r"trauma|neglect|abuse|maltreatment|adverse\s+experiences?|"
    r"exposure\s+to\s+trauma|in\s+utero\s+exposure"
    r")\b",
    re.IGNORECASE,
)

ACADEMIC_DOMAIN_RE = re.compile(
    r"\b("
    r"academic(?:\s+weakness|\s+skills?|\s+instruction)?|"
    r"math(?:ematics)?|numerical\s+operations?|written\s+language|"
    r"reading|writing|spelling|fluency|curriculum|grade[- ]level|"
    r"specialized\s+academic|processing\s+weakness(?:es)?"
    r")\b",
    re.IGNORECASE,
)

HEALTH_PLAN_SIGNAL_RE = re.compile(
    r"\b("
    r"health\s+plan|individual\s+health\s+plan|\bIHP\b|504\s+health|"
    r"medication\s+plan|nurse\s+plan|health\s+care\s+plan|"
    r"no\s+known\s+allergies|allerg(?:y|ies)\s+plan"
    r")\b",
    re.IGNORECASE,
)

BEHAVIORAL_SUPPORT_AS_HEALTH_PLAN_RE = re.compile(
    r"\b("
    r"support\s+system|wrap[- ]?around|behavioral\s+issues?|"
    r"escalation\s+of\s+behavioral|maintaining\s+.{0,40}safety"
    r")\b",
    re.IGNORECASE,
)

SLEEP_QUALITY_RE = re.compile(
    r"\b("
    r"insomnia|night\s*terrors?|night\s*wak(?:e|ing)|"
    r"CPAP|sleep\s+study|sleep\s+plan|bedtime|"
    r"poor\s+sleep|good\s+sleep|sleep\s+(?:quality|pattern|difficulty|difficulties|hygiene)|"
    r"sleeps?\s+(?:poorly|well|through|ok|okay|fine)|"
    r"difficulty\s+(?:with\s+)?sleeping|trouble\s+sleeping|"
    r"sleep\s+(?:is|was|has\s+been)\s+\w+"
    r")\b",
    re.IGNORECASE,
)

TRANSIENT_FATIGUE_RE = re.compile(
    r"("
    r"\bi'?m\s+tired\b|\bi\s+am\s+tired\b|\btired\.?\s+but\s+fine\b|"
    r"\bhow\s+do\s+you\s+feel\s+today\b|\bfeel(?:ing)?\s+tired\b"
    r")",
    re.IGNORECASE,
)

INSTRUMENT_RESULT_RE = re.compile(
    r"\b("
    r"clinically\s+significant|borderline\s+clinical|clinical\s+range|"
    r"t[- ]?score|standard\s+score|percentile|composite\s+score|"
    r"above\s+average|below\s+average|average\s+range"
    r")\b",
    re.IGNORECASE,
)


def _blob(value: str | None, value_text: str | None) -> str:
    return f"{value_text or ''} {value or ''}".strip()


def has_developmental_domain(value: str | None, value_text: str | None) -> bool:
    """True when the claim's content is structurally developmental (not academic)."""

    text = _blob(value, value_text)
    if not text:
        return False
    if ACADEMIC_DOMAIN_RE.search(text) and not DEVELOPMENTAL_DOMAIN_RE.search(text):
        return False
    # Section-heading boilerplate ("developmental history is remarkable for…")
    # is not itself developmental content when the substance is trauma.
    if TRAUMA_NARRATIVE_RE.search(text) and not DEVELOPMENTAL_DOMAIN_RE.search(text):
        return False
    return bool(DEVELOPMENTAL_DOMAIN_RE.search(text))


def is_academic_as_developmental_history(value: str | None, value_text: str | None) -> bool:
    text = _blob(value, value_text)
    if not text:
        return False
    return bool(ACADEMIC_DOMAIN_RE.search(text)) and not bool(
        DEVELOPMENTAL_DOMAIN_RE.search(text)
    )


def is_trauma_as_developmental_history(value: str | None, value_text: str | None) -> bool:
    """Trauma narrative mistagged as developmental_history (belongs on trauma_history)."""

    text = _blob(value, value_text)
    if not text:
        return False
    if not TRAUMA_NARRATIVE_RE.search(text):
        return False
    # Keep when the claim also states a developmental course (e.g. delays after trauma).
    return not bool(DEVELOPMENTAL_DOMAIN_RE.search(text))


def is_unsupported_developmental_status_value(
    value: str | None, value_text: str | None
) -> bool:
    """Drop status tokens (e.g. value=typical) whose value_text does not support them."""

    token = re.sub(r"\s+", " ", (value or "").strip().lower())
    if token not in {"typical", "atypical", "delayed", "normal", "age-appropriate"}:
        return False
    vt = value_text or ""
    if token == "typical" and re.search(
        r"\b(typical|on\s+time|within\s+normal|age[- ]appropriate|no\s+delays?)\b",
        vt,
        re.IGNORECASE,
    ):
        return False
    if token in {"atypical", "delayed"} and re.search(
        rf"\b{re.escape(token)}\b|\bdelays?\b|\bmilestones?\b",
        vt,
        re.IGNORECASE,
    ):
        return False
    if token in {"normal", "age-appropriate"} and re.search(
        r"\b(normal|age[- ]appropriate|typical|on\s+time)\b",
        vt,
        re.IGNORECASE,
    ):
        return False
    return True


def is_sleep_content_as_health_plan(value: str | None, value_text: str | None) -> bool:
    """CPAP / sleep-study narrative mistagged as health_plan_status."""

    text = _blob(value, value_text)
    if not text:
        return False
    if HEALTH_PLAN_SIGNAL_RE.search(text):
        return False
    return bool(
        re.search(r"\b(CPAP|sleep\s+study|sleep\s+plan|fitted\s+for\s+a\s+CPAP)\b", text, re.I)
    )


def is_academic_as_behavioral_concern(value: str | None, value_text: str | None) -> bool:
    """Academic skill weakness mistagged as behavioral_concern."""

    text = _blob(value, value_text)
    if not text:
        return False
    if not ACADEMIC_DOMAIN_RE.search(text):
        return False
    # Real behavior language keeps the fact even if academics are mentioned.
    if re.search(
        r"\b(meltdown|aggression|defian|off[- ]task|disrupt|tantrum|elop|"
        r"hit(?:ting)?|scream|inconsolable|behavioral)\b",
        text,
        re.IGNORECASE,
    ):
        return False
    return True


def is_behavioral_support_as_health_plan(value: str | None, value_text: str | None) -> bool:
    """True when a behavioral/wrap support sentence was bagged as health_plan_status."""

    text = _blob(value, value_text)
    if not text:
        return False
    if HEALTH_PLAN_SIGNAL_RE.search(text):
        return False
    return bool(BEHAVIORAL_SUPPORT_AS_HEALTH_PLAN_RE.search(text))


def is_transient_fatigue_as_sleep(value: str | None, value_text: str | None) -> bool:
    """Feeling tired in conversation is not, by itself, a sleep-quality claim."""

    text = _blob(value, value_text)
    if not text:
        return False
    # Explicit sleep-quality / sleep-pattern language keeps the fact.
    if SLEEP_QUALITY_RE.search(text):
        return False
    if TRANSIENT_FATIGUE_RE.search(text):
        return True
    # Bare value "tired" / "fatigue" without sleep-quality language.
    compact = re.sub(r"\s+", " ", (value or "").strip().lower())
    if compact in {"tired", "fatigue", "fatigued", "sleepy"}:
        return True
    return False


def is_instrument_result_text(value: str | None, value_text: str | None) -> bool:
    return bool(INSTRUMENT_RESULT_RE.search(_blob(value, value_text)))


# --- Compile preflight ---

HEADER_ONLY_PREDICATES = frozenset({"legal_name", "dob", "age_years"})


@dataclass(frozen=True, slots=True)
class ExclusionRecord:
    fact_id: str
    predicate: str
    destination: str
    reason: str
    source_id: str
    source_label: str
    source_date: str | None
    as_of_date: str | None
    value_text: str


@dataclass
class EvidencePreflight:
    """Eligible facts plus review-queue / exclusion audit for one selection pass."""

    eligible: list[Fact] = field(default_factory=list)
    review_queue: list[ExclusionRecord] = field(default_factory=list)
    exclusions: list[ExclusionRecord] = field(default_factory=list)


def _source_meta(ledger: Ledger) -> dict[str, Source]:
    return {s.id: s for s in ledger.sources}


def fact_anchor_date(fact: Fact) -> str | None:
    return fact.as_of_date or fact.source_date


def is_future_of_evaluation(fact: Fact, evaluation_date: str | None) -> bool:
    if not evaluation_date:
        return False
    anchor = fact_anchor_date(fact)
    if not anchor:
        return False
    return anchor > evaluation_date


def dedupe_facts(facts: Iterable[Fact]) -> list[Fact]:
    """Keep first occurrence of identical (predicate, value, source_id, assertion)."""

    seen: set[tuple] = set()
    out: list[Fact] = []
    for fact in facts:
        key = (fact.predicate, fact.value, fact.source_id, fact.assertion, fact.qualifier)
        if key in seen:
            continue
        seen.add(key)
        out.append(fact)
    return out


def preflight_facts(
    facts: Iterable[Fact],
    ledger: Ledger,
    *,
    destination: str,
    exclude_header_only: bool = True,
    require_developmental_domain_for_catch_all: bool = False,
) -> EvidencePreflight:
    """Apply drafting gates; never silently delete — exclusions/review are recorded."""

    sources = _source_meta(ledger)
    evaluation_date = ledger.child.evaluation_date
    result = EvidencePreflight()
    for fact in dedupe_facts(facts):
        src = sources.get(fact.source_id)
        label = src.label if src is not None else fact.source_id
        src_date = src.date if src is not None else fact.source_date

        def _rec(reason: str) -> ExclusionRecord:
            return ExclusionRecord(
                fact_id=fact.id,
                predicate=fact.predicate,
                destination=destination,
                reason=reason,
                source_id=fact.source_id,
                source_label=label,
                source_date=src_date,
                as_of_date=fact.as_of_date,
                value_text=(fact.value_text or fact.value or "")[:240],
            )

        if exclude_header_only and fact.predicate in HEADER_ONLY_PREDICATES:
            result.exclusions.append(_rec("header_only_identity_or_current_age"))
            continue

        if is_future_of_evaluation(fact, evaluation_date):
            result.review_queue.append(
                _rec("as_of_or_source_date_after_evaluation_date")
            )
            continue

        if (
            require_developmental_domain_for_catch_all
            and fact.predicate == "developmental_history"
            and not has_developmental_domain(fact.value, fact.value_text)
        ):
            result.exclusions.append(
                _rec("developmental_history_lacks_structural_developmental_domain")
            )
            continue

        if fact.predicate == "developmental_history" and is_academic_as_developmental_history(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("academic_content_as_developmental_history"))
            continue

        if fact.predicate == "developmental_history" and is_trauma_as_developmental_history(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("trauma_narrative_as_developmental_history"))
            continue

        if fact.predicate == "developmental_history" and is_unsupported_developmental_status_value(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("unsupported_developmental_status_value"))
            continue

        if fact.predicate == "behavioral_concern" and is_academic_as_behavioral_concern(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("academic_content_as_behavioral_concern"))
            continue

        if fact.predicate == "health_plan_status" and is_behavioral_support_as_health_plan(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("behavioral_support_as_health_plan_status"))
            continue

        if fact.predicate == "health_plan_status" and is_sleep_content_as_health_plan(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("sleep_content_as_health_plan_status"))
            continue

        if fact.predicate == "sleep" and is_transient_fatigue_as_sleep(
            fact.value, fact.value_text
        ):
            result.exclusions.append(_rec("transient_fatigue_as_sleep"))
            continue

        result.eligible.append(fact)
    return result


@dataclass(frozen=True, slots=True)
class EvidenceEpisode:
    episode_id: str
    source_id: str
    source_label: str
    source_date: str | None
    as_of_date: str | None
    source_section: str | None
    fact_ids: tuple[str, ...]


def group_source_local_episodes(
    facts: list[Fact],
    ledger: Ledger,
) -> list[EvidenceEpisode]:
    """Group related facts by source + date + section; preserve ledger adjacency."""

    if not facts:
        return []
    sources = _source_meta(ledger)

    def _sort_key(f: Fact) -> tuple:
        # Preserve extraction order within a source via numeric id suffix when present.
        m = re.search(r"_(\d+)$", f.id)
        seq = int(m.group(1)) if m else 0
        return (f.source_id, fact_anchor_date(f) or "", f.source_section or "", seq, f.id)

    ordered = sorted(facts, key=_sort_key)
    episodes: list[EvidenceEpisode] = []
    current_key: tuple | None = None
    bucket: list[Fact] = []

    def _flush() -> None:
        nonlocal bucket, current_key
        if not bucket or current_key is None:
            bucket = []
            return
        src_id, anchor, section = current_key
        src = sources.get(src_id)
        episodes.append(
            EvidenceEpisode(
                episode_id=f"ep_{src_id}_{len(episodes)+1:02d}",
                source_id=src_id,
                source_label=src.label if src is not None else src_id,
                source_date=src.date if src is not None else bucket[0].source_date,
                as_of_date=anchor or None,
                source_section=section or None,
                fact_ids=tuple(f.id for f in bucket),
            )
        )
        bucket = []

    for fact in ordered:
        key = (fact.source_id, fact_anchor_date(fact) or "", fact.source_section or "")
        if current_key is None:
            current_key = key
            bucket = [fact]
            continue
        if key != current_key:
            _flush()
            current_key = key
            bucket = [fact]
        else:
            bucket.append(fact)
    _flush()
    return episodes


def attribution_for_fact(fact: Fact, ledger: Ledger) -> dict[str, str | None]:
    """Human-readable attribution: named reporter when present, else source label."""

    sources = _source_meta(ledger)
    src = sources.get(fact.source_id)
    reporter = (fact.reporter or "").strip() or None
    return {
        "reporter": reporter,
        "source_id": fact.source_id,
        "source_label": src.label if src is not None else fact.source_id,
        "source_date": src.date if src is not None else fact.source_date,
        "as_of_date": fact.as_of_date,
        "attribution": reporter or (src.label if src is not None else fact.source_id),
    }


def variance_is_meaningful(versions: list[dict]) -> bool:
    """A single perspectival fact is not a variance set."""

    if len(versions) < 2:
        return False
    informants = {
        (v.get("reporter") or "").strip().lower()
        or (v.get("source_id") or "")
        for v in versions
    }
    if len(informants) < 2:
        return False
    values = {(v.get("value"), v.get("assertion")) for v in versions}
    return len(values) >= 2
