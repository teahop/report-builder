"""Focused tests for span→id alignment. No live model."""

from __future__ import annotations

from history_align import (
    align_prose_to_facts,
    match_fact_to_span,
    strip_id_artifacts,
)
from test_history_draft import _mini_ledger


def _by_id(ledger):
    return {f.id: f for f in ledger.facts}


def test_aligner_maps_content_not_visible_ids() -> None:
    ledger = _mini_ledger()
    facts = [f for f in ledger.facts if f.id in {"f_walk_1", "f_fam_1", "f_allergy_1"}]
    prose = (
        "Jordan walked at 18 months (f_fam_1). "
        "A maternal uncle has ADHD. "
        "There is a known peanut allergy (fact_ids: f_walk_1)."
    )
    statements = align_prose_to_facts(prose, facts, exclude_name=ledger.child.name)
    by_quote = {s.quote: s.fact_ids for s in statements}

    walk_ids = next(ids for quote, ids in by_quote.items() if "18 months" in quote)
    assert walk_ids == ["f_walk_1"], walk_ids
    fam_ids = next(ids for quote, ids in by_quote.items() if "uncle" in quote)
    assert fam_ids == ["f_fam_1"], fam_ids
    allergy_ids = next(ids for quote, ids in by_quote.items() if "peanut" in quote)
    assert allergy_ids == ["f_allergy_1"], allergy_ids
    # Visible ids in the wrong sentence must not hijack the mapping.
    assert "f_fam_1" not in walk_ids
    assert "f_walk_1" not in allergy_ids


def test_aligner_omits_unmatched_rather_than_guessing() -> None:
    ledger = _mini_ledger()
    walk = _by_id(ledger)["f_walk_1"]
    prose = "Jordan enjoys drawing and plays soccer after school."
    assert match_fact_to_span(walk, prose) is False
    assert align_prose_to_facts(prose, [walk], exclude_name=ledger.child.name) == []


def test_fused_span_may_carry_several_fact_ids() -> None:
    ledger = _mini_ledger()
    facts = [_by_id(ledger)[i] for i in ("f_walk_1", "f_prior_1")]
    prose = (
        "A prior eval noted speech delay, and she was walking at 18 months."
    )
    statements = align_prose_to_facts(prose, facts, exclude_name=ledger.child.name)
    assert len(statements) == 1
    assert set(statements[0].fact_ids) == {"f_walk_1", "f_prior_1"}


def test_strip_id_artifacts_leaves_claim_text() -> None:
    raw = (
        "Emma walked at 19 months (f_doc_26_006) and neglect was suspected "
        "(fact_ids: f_doc_26_008, f_doc_26_005)."
    )
    cleaned = strip_id_artifacts(raw)
    assert "f_doc_" not in cleaned
    assert "fact_ids" not in cleaned
    assert "walked at 19 months" in cleaned
    assert "neglect was suspected" in cleaned


def test_generic_shared_tokens_do_not_cross_attach() -> None:
    """Two behavioral_concern facts sharing 'scored/range/problems' stay distinct."""

    from schemas import Fact

    def _f(**kwargs) -> Fact:
        defaults = dict(
            subject="child",
            qualifier=None,
            assertion="asserted",
            source_id="src_prior",
            source_date="2013-09-10",
            as_of_date=None,
            reporter=None,
            life_stage="preschool",
            grade=None,
            temporality="durable",
            confidence="stated",
            derivation=None,
            inherits_dispute=False,
            valence="neutral",
            source_section=None,
        )
        defaults.update(kwargs)
        return Fact(**defaults)

    f013 = _f(
        id="f_013",
        predicate="behavioral_concern",
        value="borderline clinical range for emotional reactivity and oppositional defiant problems",
        value_text="scored in the borderline clinical range for emotional reactivity and oppositional defiant problems",
    )
    f014 = _f(
        id="f_014",
        predicate="behavioral_concern",
        value="clinically significant range for somatic complaints, withdrawal, and social development problems",
        value_text="scored in the clinically significant range for somatic complaints, withdrawal, and social development problems",
    )
    f008 = _f(
        id="f_008",
        predicate="family_history",
        value="history of neglect, trauma suspected",
        value_text="History of trauma (including abuse, neglect, molest, or domestic violence): Yes of neglect, trauma suspected.",
    )
    s013 = (
        "Emma scored in the borderline clinical range for emotional reactivity "
        "and oppositional defiant problems."
    )
    s014 = (
        "She scored in the clinically significant range for somatic complaints, "
        "withdrawal, and social development problems."
    )
    speech = (
        'Concerns included "delays in speech and language, suspected delays in '
        'overall cognitive development."'
    )
    assert match_fact_to_span(f013, s013) is True
    assert match_fact_to_span(f014, s014) is True
    assert match_fact_to_span(f013, s014) is False
    assert match_fact_to_span(f014, s013) is False
    assert match_fact_to_span(f008, speech) is False
    family = 'Family history indicating "history of neglect, trauma suspected."'
    assert match_fact_to_span(f008, family) is True


def test_shared_percent_does_not_cross_topic() -> None:
    from schemas import Fact

    def _f(**kwargs) -> Fact:
        defaults = dict(
            subject="child",
            qualifier=None,
            assertion="asserted",
            source_id="src_school",
            source_date="2024-10-02",
            as_of_date="2024-10-02",
            reporter=None,
            life_stage="school-age",
            grade="4",
            temporality="as_of",
            confidence="stated",
            derivation=None,
            inherits_dispute=False,
            valence="neutral",
            source_section=None,
        )
        defaults.update(kwargs)
        return Fact(**defaults)

    math75 = _f(
        id="f_math_75",
        predicate="math_fluency",
        value="75",
        value_text="at least 75% accuracy in 1/2 trials",
    )
    math90 = _f(
        id="f_math_90",
        predicate="math_fluency",
        value="90",
        value_text="at least 90% accuracy in 1/2 trials as measured by student work samples/teacher records.",
    )
    write75 = _f(
        id="f_write_75",
        predicate="written_expression",
        value="75",
        value_text="with at least 75% accuracy as measured by student work samples.",
    )
    math_span = (
        "She demonstrates math fluency with at least 75% accuracy in some trials, "
        "progressing to 90% accuracy as measured by student work samples."
    )
    adapt = (
        "According to the current IEP records dated October 2, 2024, her "
        "behavioral adaptation is average."
    )
    ids = {
        s.quote: s.fact_ids
        for s in align_prose_to_facts(
            math_span + " " + adapt,
            [math75, math90, write75],
            exclude_name="Jordan Avery Quinn",
        )
    }
    math_ids = next(v for k, v in ids.items() if "math fluency" in k)
    assert "f_write_75" not in math_ids
    assert "f_math_75" in math_ids
    assert "f_math_90" in math_ids
    assert all("behavioral adaptation" not in k for k in ids)


if __name__ == "__main__":
    tests = [
        test_aligner_maps_content_not_visible_ids,
        test_aligner_omits_unmatched_rather_than_guessing,
        test_fused_span_may_carry_several_fact_ids,
        test_strip_id_artifacts_leaves_claim_text,
        test_generic_shared_tokens_do_not_cross_attach,
        test_shared_percent_does_not_cross_topic,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
