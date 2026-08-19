"""No silent disposition: every registered predicate is selected, header-only, provenance, or listed."""

from __future__ import annotations

from history_evidence import HEADER_ONLY_PREDICATES
from history_selectors import (
    DELIBERATELY_UNWIRED_PREDICATES,
    headed_selector_predicates,
)
from predicates import PREDICATE_VOCABULARY, PROVENANCE_PREDICATES


def test_every_registered_predicate_has_a_disposition() -> None:
    registered = {spec.name for spec in PREDICATE_VOCABULARY}
    accounted = (
        headed_selector_predicates()
        | HEADER_ONLY_PREDICATES
        | PROVENANCE_PREDICATES
        | frozenset(DELIBERATELY_UNWIRED_PREDICATES)
    )
    missing = registered - accounted
    assert missing == set(), (
        "registered predicates with no selector, header-only, provenance, "
        f"or deliberately-unwired reason: {sorted(missing)}"
    )


def test_deliberately_unwired_entries_have_reasons() -> None:
    for name, reason in DELIBERATELY_UNWIRED_PREDICATES.items():
        assert reason.strip(), f"{name} is unwired with an empty reason"


def test_unwired_reason_cannot_replace_a_selector() -> None:
    overlap = headed_selector_predicates() & frozenset(DELIBERATELY_UNWIRED_PREDICATES)
    assert overlap == set(), f"listed as unwired but also selected: {sorted(overlap)}"


def test_group_a_collapses_to_qualified_generics() -> None:
    from predicates import PREDICATES

    names = set(PREDICATES)
    banned = {
        "low_incidence_services_requirement",
        "low_incidence_services_status",
        "assistive_technology_requirement",
        "primary_language_support_requirement",
        "visual_impairment_status",
        "hearing_impairment_status",
        "executive_functioning_deficit",
        "adaptive_functioning_deficit",
    }
    assert banned.isdisjoint(names)
    for generic in ("service_requirement", "impairment_status", "functioning_deficit"):
        assert PREDICATES[generic].takes_qualifier


def test_group_b_and_d_keepers_are_registered() -> None:
    from history_selectors import (
        EDUCATIONAL_IEP_PREDICATES,
        EDUCATIONAL_SCHOOL_EXPERIENCE_PREDICATES,
        EDUCATIONAL_SCHOOL_HISTORY_PREDICATES,
        FAMILY_HISTORY_PREDICATES,
        SOCIAL_HISTORY_PREDICATES,
    )
    from predicates import PREDICATES

    keepers = {
        "anticipated_graduation_date",
        "alternative_diploma_pathway_eligibility",
        "caaspp_participation",
        "conservatorship_status",
        "peer_relationships",
        "skill_generalization",
        "parental_limitations",
    }
    rejected = {
        "unsafe_behaviors_at_home",
        "school_setting_success",
        "english_learner_status",
        "behavior_impedes_learning",
        "diagnosis_list",
    }
    assert keepers <= set(PREDICATES)
    assert rejected.isdisjoint(PREDICATES)
    for name in (
        "anticipated_graduation_date",
        "alternative_diploma_pathway_eligibility",
        "caaspp_participation",
        "conservatorship_status",
    ):
        assert PREDICATES[name].predicate_class == "record"
        assert PREDICATES[name].default_temporality == "as_of"
    for name in ("peer_relationships", "skill_generalization", "parental_limitations"):
        assert PREDICATES[name].predicate_class == "perspectival"
        assert PREDICATES[name].default_temporality == "as_of"
    assert "anticipated_graduation_date" in EDUCATIONAL_SCHOOL_HISTORY_PREDICATES
    assert "caaspp_participation" in EDUCATIONAL_SCHOOL_HISTORY_PREDICATES
    assert "alternative_diploma_pathway_eligibility" in EDUCATIONAL_IEP_PREDICATES
    assert "conservatorship_status" in FAMILY_HISTORY_PREDICATES
    assert "parental_limitations" in FAMILY_HISTORY_PREDICATES
    assert SOCIAL_HISTORY_PREDICATES == frozenset({"peer_relationships"})
    assert "skill_generalization" in EDUCATIONAL_SCHOOL_EXPERIENCE_PREDICATES
