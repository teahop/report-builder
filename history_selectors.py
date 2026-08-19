"""Explicit History fact selectors — predicate / source / reporter identity only.

No substring guessing over prose. Unknown nurse sources and unsupported social
predicates surface as empty selections (gaps recorded by the compiler).

Catch-all `developmental_history` is never automatic Birth/Developmental evidence
unless the value's domain is structurally developmental. Prior-evaluation selection
uses an explicit synthesis contract — not every fact from a prior_eval source.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from history_evidence import (
    HEADER_ONLY_PREDICATES,
    has_developmental_domain,
    is_instrument_result_text,
    preflight_facts,
)
from schemas import Fact, Ledger, Source

# --- Registered predicate menus (composed from predicates.py vocabulary) ---

FAMILY_HISTORY_PREDICATES = frozenset({"family_history"})

# Specific developmental predicates are automatic; catch-all is domain-gated.
BIRTH_DEVELOPMENTAL_SPECIFIC = frozenset(
    {
        "pregnancy_course",
        "birth_term",
        "birth_delivery",
        "nicu",
        "walked_age_months",
        "first_words_age_months",
        "two_word_phrases_age_months",
        "developmental_concern_onset",
        "trauma_history",
    }
)

BIRTH_DEVELOPMENTAL_CATCH_ALL = frozenset({"developmental_history"})

HEALTH_HISTORY_PREDICATES = frozenset(
    {
        "allergy_status",
        "allergy_substance",
        "health_plan_status",
        "medications",
        "hospitalizations",
        "sleep",
    }
)

# No registered social-relationship / social-activity predicates yet.
SOCIAL_HISTORY_PREDICATES = frozenset()

EDUCATIONAL_SCHOOL_HISTORY_PREDICATES = frozenset(
    {
        "grade",
        "school_enrollment",
        "attendance",
        "retention_year",
        "basic_reading",
        "reading_level",
        "reading_fluency",
        "reading_comprehension",
        "spelling",
        "written_expression",
        "writing_fluency",
        "math_computation",
        "math_fluency",
        "math_reasoning",
    }
)

EDUCATIONAL_SCHOOL_EXPERIENCE_PREDICATES = frozenset(
    {
        "grade",
        "school_enrollment",
        "attendance",
        "retention_year",
        "preschool_experience_impression",
        "basic_reading",
        "reading_level",
        "reading_fluency",
        "reading_comprehension",
        "spelling",
        "written_expression",
        "writing_fluency",
        "math_computation",
        "math_fluency",
        "math_reasoning",
        "behavioral_referral",
        "classroom_engagement",
        "classroom_engagement_impression",
        "homework_completion_impression",
        "anxiety_impression",
        "inattention_rating",
        "hyperactivity_rating",
        "testing_impression",
        "interview_impression",
    }
)

EDUCATIONAL_INTERVENTION_PREDICATES = frozenset({"intervention_tier", "private_tutoring"})

EDUCATIONAL_IEP_PREDICATES = frozenset({"iep_status", "plan_504_status"})

# Provisional; vocabulary has no covid-education predicate.
COVID_EDUCATIONAL_PREDICATES = frozenset()

# Current-evaluation score reports must not enter History as prior evaluations.
SCORE_REPORT_DOC_CLASS = "score_report"

# Explicit prior-evaluation synthesis contract (not "all facts from prior_eval").
# Principal findings, developmental/trauma notes from that eval, and score/eligibility
# outcomes. Excludes header identity, session demeanor, and undifferentiated symptom dumps
# unless they are instrument-result language.
PREVIOUS_EVALUATION_SYNTHESIS_PREDICATES = frozenset(
    {
        "trauma_history",
        "developmental_concern_onset",
        "developmental_history",
        "walked_age_months",
        "first_words_age_months",
        "two_word_phrases_age_months",
        "pregnancy_course",
        "birth_term",
        "birth_delivery",
        "nicu",
        "basic_reading",
        "reading_level",
        "reading_fluency",
        "reading_comprehension",
        "spelling",
        "written_expression",
        "writing_fluency",
        "math_computation",
        "math_fluency",
        "math_reasoning",
        "iep_status",
        "plan_504_status",
        "intervention_tier",
        "family_history",
        "testing_impression",
        "interview_impression",
    }
)

# behavioral_concern may enter prior-eval only when it carries instrument-result language.
PREVIOUS_EVALUATION_CONDITIONAL_PREDICATES = frozenset({"behavioral_concern"})

# Registered names that are not selected into a headed History block, with a
# reason. An empty reason is not allowed — silence is the §9.4a violation.
DELIBERATELY_UNWIRED_PREDICATES: dict[str, str] = {
    "referral_reason": (
        "Served by the Reason for Referral path, not a History section selector."
    ),
}


def headed_selector_predicates() -> frozenset[str]:
    """Every predicate a History selector frozenset can currently read."""

    return (
        FAMILY_HISTORY_PREDICATES
        | BIRTH_DEVELOPMENTAL_SPECIFIC
        | BIRTH_DEVELOPMENTAL_CATCH_ALL
        | HEALTH_HISTORY_PREDICATES
        | SOCIAL_HISTORY_PREDICATES
        | EDUCATIONAL_SCHOOL_HISTORY_PREDICATES
        | EDUCATIONAL_SCHOOL_EXPERIENCE_PREDICATES
        | EDUCATIONAL_INTERVENTION_PREDICATES
        | EDUCATIONAL_IEP_PREDICATES
        | COVID_EDUCATIONAL_PREDICATES
        | PREVIOUS_EVALUATION_SYNTHESIS_PREDICATES
        | PREVIOUS_EVALUATION_CONDITIONAL_PREDICATES
    )


@dataclass(frozen=True, slots=True)
class RaterIdentity:
    """Stable identity for one caregiver / teacher / student input block."""

    rater_id: str
    role: str  # caregiver | teacher | student
    display_name: str
    source_ids: tuple[str, ...] = ()


@dataclass
class SelectorResult:
    facts: list[Fact] = field(default_factory=list)
    rater: RaterIdentity | None = None
    exclusions: list = field(default_factory=list)
    review_queue: list = field(default_factory=list)


def _source_by_id(ledger: Ledger) -> dict[str, Source]:
    return {s.id: s for s in ledger.sources}


def _apply_preflight(
    facts: list[Fact],
    ledger: Ledger,
    *,
    destination: str,
    exclude_header_only: bool = True,
    require_developmental_domain_for_catch_all: bool = False,
) -> SelectorResult:
    pf = preflight_facts(
        facts,
        ledger,
        destination=destination,
        exclude_header_only=exclude_header_only,
        require_developmental_domain_for_catch_all=require_developmental_domain_for_catch_all,
    )
    return SelectorResult(
        facts=pf.eligible,
        exclusions=list(pf.exclusions),
        review_queue=list(pf.review_queue),
    )


def _facts_with_predicates(ledger: Ledger, predicates: frozenset[str]) -> list[Fact]:
    if not predicates:
        return []
    return [f for f in ledger.facts if f.predicate in predicates]


def select_family_history(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, FAMILY_HISTORY_PREDICATES),
        ledger,
        destination="family_history",
    )


def select_birth_developmental_history(ledger: Ledger) -> SelectorResult:
    """Specific developmental predicates + domain-gated developmental_history catch-all."""

    specific = _facts_with_predicates(ledger, BIRTH_DEVELOPMENTAL_SPECIFIC)
    catch_all_raw = _facts_with_predicates(ledger, BIRTH_DEVELOPMENTAL_CATCH_ALL)
    catch_all: list[Fact] = []
    rejected_catch_all: list[Fact] = []
    for fact in catch_all_raw:
        if has_developmental_domain(fact.value, fact.value_text):
            catch_all.append(fact)
        else:
            rejected_catch_all.append(fact)
    result = _apply_preflight(
        specific + catch_all,
        ledger,
        destination="birth_developmental_history",
        require_developmental_domain_for_catch_all=True,
    )
    from history_evidence import ExclusionRecord, is_academic_as_developmental_history, is_trauma_as_developmental_history

    sources = _source_by_id(ledger)
    for fact in rejected_catch_all:
        src = sources.get(fact.source_id)
        if is_academic_as_developmental_history(fact.value, fact.value_text):
            reason = "academic_content_as_developmental_history"
        elif is_trauma_as_developmental_history(fact.value, fact.value_text):
            reason = "trauma_narrative_as_developmental_history"
        else:
            reason = "developmental_history_lacks_structural_developmental_domain"
        result.exclusions.append(
            ExclusionRecord(
                fact_id=fact.id,
                predicate=fact.predicate,
                destination="birth_developmental_history",
                reason=reason,
                source_id=fact.source_id,
                source_label=src.label if src is not None else fact.source_id,
                source_date=src.date if src is not None else fact.source_date,
                as_of_date=fact.as_of_date,
                value_text=(fact.value_text or fact.value or "")[:240],
            )
        )
    return result


def select_health_history(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, HEALTH_HISTORY_PREDICATES),
        ledger,
        destination="health_history",
    )


def select_social_history(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, SOCIAL_HISTORY_PREDICATES),
        ledger,
        destination="social_history",
    )


def select_nurse_report(ledger: Ledger) -> SelectorResult:
    """Nurse Report requires an explicit nurse source type — not currently modeled."""

    del ledger
    return SelectorResult(facts=[])


def select_educational_school_history(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, EDUCATIONAL_SCHOOL_HISTORY_PREDICATES),
        ledger,
        destination="educational_school_history",
    )


def select_educational_school_experience(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, EDUCATIONAL_SCHOOL_EXPERIENCE_PREDICATES),
        ledger,
        destination="educational_school_experience",
    )


def select_educational_intervention(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, EDUCATIONAL_INTERVENTION_PREDICATES),
        ledger,
        destination="educational_intervention",
    )


def select_educational_iep(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, EDUCATIONAL_IEP_PREDICATES),
        ledger,
        destination="educational_iep",
    )


def select_covid_educational_experience(ledger: Ledger) -> SelectorResult:
    return _apply_preflight(
        _facts_with_predicates(ledger, COVID_EDUCATIONAL_PREDICATES),
        ledger,
        destination="covid_educational_experience",
    )


def _prior_eval_candidate(fact: Fact) -> bool:
    if fact.predicate in HEADER_ONLY_PREDICATES:
        return False
    if fact.predicate in PREVIOUS_EVALUATION_SYNTHESIS_PREDICATES:
        if fact.predicate == "developmental_history":
            return has_developmental_domain(fact.value, fact.value_text)
        return True
    if fact.predicate in PREVIOUS_EVALUATION_CONDITIONAL_PREDICATES:
        return is_instrument_result_text(fact.value, fact.value_text)
    return False


def select_previous_evaluations(ledger: Ledger) -> SelectorResult:
    """Prior-evaluation synthesis contract; never current score reports or header IDs."""

    sources = _source_by_id(ledger)
    candidates: list[Fact] = []
    rejected: list[Fact] = []
    for fact in ledger.facts:
        src = sources.get(fact.source_id)
        if src is None:
            continue
        if src.doc_class == SCORE_REPORT_DOC_CLASS:
            continue
        if src.type != "prior_eval":
            continue
        if _prior_eval_candidate(fact):
            candidates.append(fact)
        else:
            rejected.append(fact)

    result = _apply_preflight(
        candidates,
        ledger,
        destination="previous_evaluations",
        exclude_header_only=True,
        require_developmental_domain_for_catch_all=True,
    )
    # Record contract rejects (not future-dated — those go through preflight).
    for fact in rejected:
        src = sources.get(fact.source_id)
        from history_evidence import ExclusionRecord

        result.exclusions.append(
            ExclusionRecord(
                fact_id=fact.id,
                predicate=fact.predicate,
                destination="previous_evaluations",
                reason="outside_prior_evaluation_synthesis_contract",
                source_id=fact.source_id,
                source_label=src.label if src is not None else fact.source_id,
                source_date=src.date if src is not None else fact.source_date,
                as_of_date=fact.as_of_date,
                value_text=(fact.value_text or fact.value or "")[:240],
            )
        )
    return result


def _normalize_person_key(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _role_for_source(source: Source) -> str | None:
    if source.type == "parent":
        return "caregiver"
    if source.type == "teacher":
        return "teacher"
    if source.type == "observation":
        return "student"
    return None


def _display_for_rater(role: str, name: str) -> str:
    if role == "caregiver":
        return f"Parent/Caregiver Input — {name}"
    if role == "teacher":
        return f"Teacher Input — {name}"
    if role == "student":
        return f"Student/Client/Patient Input — {name}"
    return name


def _block_key_for_rater(role: str, rater_id: str) -> str:
    return f"{role}_input:{rater_id}"


def discover_raters(ledger: Ledger) -> list[RaterIdentity]:
    """
    Explicit rater identities from reporter field and interview-capable sources.

    - Facts with an explicit `reporter` consolidate under that person.
    - Narrative parent / teacher / observation sources without a reporter become
      their own rater keyed by source id (no label substring guessing).
    - Score-report sources never create interview/input blocks.
    """

    sources = _source_by_id(ledger)
    by_key: dict[str, dict] = {}

    def _add(
        *,
        key: str,
        role: str,
        display_name: str,
        source_id: str,
    ) -> None:
        row = by_key.get(key)
        if row is None:
            by_key[key] = {
                "rater_id": key,
                "role": role,
                "display_name": display_name,
                "source_ids": {source_id},
            }
        else:
            row["source_ids"].add(source_id)

    for fact in ledger.facts:
        src = sources.get(fact.source_id)
        if src is not None and src.doc_class == SCORE_REPORT_DOC_CLASS:
            continue
        reporter = (fact.reporter or "").strip()
        if reporter:
            role = "caregiver"
            if src is not None:
                mapped = _role_for_source(src)
                if mapped:
                    role = mapped
            key = _normalize_person_key(reporter)
            _add(key=key, role=role, display_name=reporter, source_id=fact.source_id)

    for source in ledger.sources:
        if source.doc_class == SCORE_REPORT_DOC_CLASS:
            continue
        role = _role_for_source(source)
        if role is None:
            continue
        # Prefer consolidation under an existing reporter when any fact on this
        # source already named one; otherwise key by source id.
        named = [
            (f.reporter or "").strip()
            for f in ledger.facts
            if f.source_id == source.id and (f.reporter or "").strip()
        ]
        if named:
            for name in named:
                key = _normalize_person_key(name)
                _add(key=key, role=role, display_name=name, source_id=source.id)
        else:
            # Only open a rater block when the source contributed non-header facts.
            contributed = [
                f
                for f in ledger.facts
                if f.source_id == source.id and f.predicate not in HEADER_ONLY_PREDICATES
            ]
            if not contributed:
                continue
            key = source.id
            _add(
                key=key,
                role=role,
                display_name=source.label,
                source_id=source.id,
            )

    raters: list[RaterIdentity] = []
    for key in sorted(by_key.keys()):
        row = by_key[key]
        raters.append(
            RaterIdentity(
                rater_id=row["rater_id"],
                role=row["role"],
                display_name=row["display_name"],
                source_ids=tuple(sorted(row["source_ids"])),
            )
        )
    return raters


def select_facts_for_rater(ledger: Ledger, rater: RaterIdentity) -> list[Fact]:
    """Facts attributable to this rater — by reporter name or source membership."""

    sources = _source_by_id(ledger)
    source_ids = set(rater.source_ids)
    name_key = _normalize_person_key(rater.display_name)
    out: list[Fact] = []
    for fact in ledger.facts:
        src = sources.get(fact.source_id)
        if src is not None and src.doc_class == SCORE_REPORT_DOC_CLASS:
            continue
        reporter = (fact.reporter or "").strip()
        if reporter and _normalize_person_key(reporter) == name_key:
            out.append(fact)
            continue
        if fact.source_id in source_ids and not reporter:
            # Source-attributed when no competing named reporter on the fact.
            out.append(fact)
    return out


def select_rater_input(ledger: Ledger) -> list[tuple[RaterIdentity, list[Fact], SelectorResult]]:
    pairs: list[tuple[RaterIdentity, list[Fact], SelectorResult]] = []
    for rater in discover_raters(ledger):
        raw = select_facts_for_rater(ledger, rater)
        result = _apply_preflight(
            raw,
            ledger,
            destination=f"rater_input:{rater.rater_id}",
            exclude_header_only=True,
        )
        substantive = [
            f for f in result.facts if f.predicate not in HEADER_ONLY_PREDICATES
        ]
        if substantive:
            pairs.append((rater, substantive, result))
    return pairs


SELECTOR_DISPATCH = {
    "family_history": select_family_history,
    "birth_developmental_history": select_birth_developmental_history,
    "health_history": select_health_history,
    "social_history": select_social_history,
    "nurse_report": select_nurse_report,
    "educational_school_history": select_educational_school_history,
    "educational_school_experience": select_educational_school_experience,
    "educational_intervention": select_educational_intervention,
    "educational_iep": select_educational_iep,
    "covid_educational_experience": select_covid_educational_experience,
    "previous_evaluations": select_previous_evaluations,
}


def run_selector(selector: str, ledger: Ledger) -> SelectorResult:
    if selector == "rater_input":
        raise ValueError("rater_input is resolved via select_rater_input()")
    fn = SELECTOR_DISPATCH.get(selector)
    if fn is None:
        raise ValueError(f"Unknown selector: {selector!r}")
    return fn(ledger)


def rater_block_key(rater: RaterIdentity) -> str:
    return _block_key_for_rater(rater.role, rater.rater_id)


def rater_display_label(rater: RaterIdentity) -> str:
    return _display_for_rater(rater.role, rater.display_name)
