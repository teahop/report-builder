"""Focused History package tests — provisional_tj_v1 boundary (no live model)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from draft import finalize_draft_output, section_has_supporting_facts
from draft_validators import render_prose_from_blocks
from history_compiler import case_brief_json, compile_history_plan, compile_section_briefs, claim_and_source_wording, format_fact_evidence_lines, render_evidence_brief_markdown
from history_draft import (
    build_history_draft_messages,
    history_system_prompt,
)
from history_fewshots import select_fewshots
from history_selectors import (
    select_birth_developmental_history,
    select_facts_for_rater,
    select_health_history,
    select_previous_evaluations,
    select_rater_input,
    discover_raters,
)
from history_structure import StructureSpecError, load_structure_spec, validate_structure_spec
from schemas import (
    Child,
    DraftBlock,
    DraftBlockKind,
    DraftCell,
    DraftProseOutput,
    DraftStatement,
    DraftTable,
    Fact,
    Ledger,
    Source,
)

_DIR = Path(__file__).resolve().parent
_STRUCTURES = _DIR / "history_structures"


def _child() -> Child:
    return Child(name="Jordan Avery Quinn", dob="2014-05-01", evaluation_date="2025-06-01")


def _fact(**kwargs) -> Fact:
    defaults = dict(
        subject="child",
        qualifier=None,
        assertion="asserted",
        as_of_date=None,
        reporter=None,
        life_stage="current",
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


def _mini_ledger() -> Ledger:
    sources = [
        Source(
            id="src_parent_a",
            type="parent",
            date="2025-01-10",
            label="Parent interview A",
            content="Parent interview notes.",
            doc_class="narrative",
        ),
        Source(
            id="src_parent_b",
            type="parent",
            date="2025-02-01",
            label="Parent interview B",
            content="Follow-up parent interview.",
            doc_class="narrative",
        ),
        Source(
            id="src_teacher",
            type="teacher",
            date="2025-02-15",
            label="Teacher interview",
            content="Teacher interview notes.",
            doc_class="narrative",
        ),
        Source(
            id="src_school",
            type="school",
            date="2025-03-01",
            label="School records",
            content="IEP and school history.",
            doc_class="narrative",
        ),
        Source(
            id="src_prior",
            type="prior_eval",
            date="2020-09-01",
            label="Prior psychoeducational evaluation",
            content="Prior eval narrative.",
            doc_class="narrative",
        ),
        Source(
            id="src_score",
            type="assessment",
            date="2025-05-01",
            label="Current WISC score report",
            content="Scores only.",
            doc_class="score_report",
        ),
    ]
    facts = [
        _fact(
            id="f_fam_1",
            predicate="family_history",
            value="maternal ADHD",
            value_text="maternal uncle with ADHD",
            qualifier="ADHD",
            reporter="Alex Quinn",
            source_id="src_parent_a",
            source_date="2025-01-10",
            life_stage="current",
            temporality="durable",
        ),
        _fact(
            id="f_walk_1",
            predicate="walked_age_months",
            value="18",
            value_text="walked at 18 months",
            reporter="Alex Quinn",
            source_id="src_parent_a",
            source_date="2025-01-10",
            life_stage="infancy",
            temporality="durable",
        ),
        _fact(
            id="f_walk_2",
            predicate="walked_age_months",
            value="18",
            value_text="also noted walking at 18 months",
            reporter="Alex Quinn",
            source_id="src_parent_b",
            source_date="2025-02-01",
            life_stage="infancy",
            temporality="durable",
        ),
        _fact(
            id="f_allergy_1",
            predicate="allergy_status",
            value="known",
            value_text="peanut allergy",
            qualifier="peanuts",
            reporter="Alex Quinn",
            source_id="src_parent_a",
            source_date="2025-01-10",
            life_stage="current",
            temporality="as_of",
            as_of_date="2025-01-10",
        ),
        _fact(
            id="f_grade_1",
            predicate="grade",
            value="4",
            value_text="fourth grade",
            source_id="src_school",
            source_date="2025-03-01",
            life_stage="school-age",
            temporality="as_of",
            as_of_date="2025-03-01",
        ),
        _fact(
            id="f_iep_1",
            predicate="iep_status",
            value="active",
            value_text="IEP in place",
            source_id="src_school",
            source_date="2025-03-01",
            life_stage="school-age",
            temporality="as_of",
            as_of_date="2025-03-01",
        ),
        _fact(
            id="f_tier_1",
            predicate="intervention_tier",
            value="tier 2",
            value_text="tier 2 reading support",
            source_id="src_school",
            source_date="2025-03-01",
            life_stage="school-age",
            temporality="as_of",
            as_of_date="2025-03-01",
        ),
        _fact(
            id="f_teacher_1",
            predicate="behavioral_concern",
            value="off-task",
            value_text="often off-task during independent work",
            source_id="src_teacher",
            source_date="2025-02-15",
            life_stage="school-age",
            temporality="as_of",
            as_of_date="2025-02-15",
        ),
        _fact(
            id="f_prior_1",
            predicate="developmental_history",
            value="speech delay",
            value_text="prior eval noted speech delay",
            source_id="src_prior",
            source_date="2020-09-01",
            life_stage="preschool",
            temporality="durable",
        ),
        # Contaminating current-test score-report fact — must not enter prior-eval History.
        _fact(
            id="f_score_1",
            predicate="basic_reading",
            value="ss 85",
            value_text="Basic Reading SS 85",
            source_id="src_score",
            source_date="2025-05-01",
            life_stage="current",
            temporality="as_of",
            as_of_date="2025-05-01",
        ),
    ]
    return Ledger(
        child=_child(),
        ledger_version="1",
        built_at="2025-06-01T00:00:00Z",
        sources=sources,
        facts=facts,
    )


def test_structure_spec_validation_rejects_duplicates_and_bad_refs() -> None:
    good = json.loads((_STRUCTURES / "provisional_tj_v1.json").read_text())
    validate_structure_spec(good)

    dup_section = copy.deepcopy(good)
    dup_section["sections"].append(copy.deepcopy(dup_section["sections"][0]))
    try:
        validate_structure_spec(dup_section)
        raise AssertionError("expected duplicate section_key to fail")
    except StructureSpecError as exc:
        assert "duplicate section_key" in str(exc)

    dup_block = copy.deepcopy(good)
    blocks = dup_block["sections"][0]["blocks"]
    blocks.append(copy.deepcopy(blocks[0]))
    try:
        validate_structure_spec(dup_block)
        raise AssertionError("expected duplicate block_key to fail")
    except StructureSpecError as exc:
        assert "duplicate block_key" in str(exc)

    bad_sel = copy.deepcopy(good)
    bad_sel["sections"][0]["blocks"][0]["selector"] = "not_a_real_selector"
    try:
        validate_structure_spec(bad_sel)
        raise AssertionError("expected unknown selector to fail")
    except StructureSpecError as exc:
        assert "unknown selector" in str(exc)


def test_provisional_tj_v1_compiles_exact_order() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    assert [s.section_key for s in plan.sections] == [
        "current_status_history",
        "educational_history",
        "previous_evaluations",
        "rater_input",
    ]
    csh = plan.sections[0]
    assert [b.block_key for b in csh.blocks] == [
        "family_history",
        "birth_developmental_history",
        "health_history",
    ]
    # social_history and nurse_report unsupported here — absent, no filler.
    # Social History now has vocabulary (peer_relationships); it stays off this
    # mini ledger because there is no such fact, not because of a schema gap.
    assert "social_history" not in {b.block_key for b in csh.blocks}
    assert "nurse_report" not in {b.block_key for b in csh.blocks}
    assert any("nurse_report" in g for g in plan.input_schema_gaps)
    assert not any(
        "social_history" in g or "Social History" in g for g in plan.input_schema_gaps
    )


def test_unsupported_blocks_absent_no_filler() -> None:
    ledger = _mini_ledger()
    # Strip family facts → family_history absent
    ledger = ledger.model_copy(
        update={"facts": [f for f in ledger.facts if f.predicate != "family_history"]}
    )
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    csh = next(s for s in plan.sections if s.section_key == "current_status_history")
    assert "family_history" not in {b.block_key for b in csh.blocks}
    assert csh.blocks  # other supported blocks remain
    for b in csh.blocks:
        assert b.fact_ids
        assert b.display_label


def test_raters_distinct_and_consolidate() -> None:
    ledger = _mini_ledger()
    raters = discover_raters(ledger)
    # Alex Quinn consolidates parent_a + parent_b interviews; teacher is distinct.
    names = {r.display_name for r in raters}
    assert "Alex Quinn" in names
    alex = next(r for r in raters if r.display_name == "Alex Quinn")
    assert set(alex.source_ids) == {"src_parent_a", "src_parent_b"}
    pairs = select_rater_input(ledger)
    keys = {r.rater_id for r, _, _ in pairs}
    assert "alex quinn" in keys
    assert any(r.role == "teacher" for r, _, _ in pairs)


def test_topic_and_rater_may_select_same_fact() -> None:
    ledger = _mini_ledger()
    topic = select_birth_developmental_history(ledger)
    health = select_health_history(ledger)
    topic_ids = {f.id for f in topic.facts} | {f.id for f in health.facts}
    rater_pairs = select_rater_input(ledger)
    alex_facts = next(facts for r, facts, _ in rater_pairs if r.display_name == "Alex Quinn")
    overlap = topic_ids.intersection({f.id for f in alex_facts})
    assert "f_walk_1" in overlap
    assert "f_allergy_1" in overlap


def test_every_occurrence_keeps_fact_id() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    csh = next(s for s in plan.sections if s.section_key == "current_status_history")
    rater = next(s for s in plan.sections if s.section_key == "rater_input")
    walk_in_topic = [
        b for b in csh.blocks if "f_walk_1" in b.fact_ids or "f_walk_2" in b.fact_ids
    ]
    walk_in_rater = [b for b in rater.blocks if "f_walk_1" in b.fact_ids]
    assert walk_in_topic and walk_in_rater
    assert "f_walk_1" in walk_in_rater[0].fact_ids


def test_reuse_context_records_without_suppressing() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    csh = next(s for s in plan.sections if s.section_key == "current_status_history")
    rater = next(s for s in plan.sections if s.section_key == "rater_input")
    from history_schemas import FactReuseRecord

    prior = [
        FactReuseRecord(
            fact_id="f_walk_1",
            section_key="current_status_history",
            block_key="birth_developmental_history",
            purpose="topic_history",
        )
    ]
    brief = json.loads(
        case_brief_json(
            plan,
            rater,
            ledger,
            conflicts=[],
            variance=[],
            reuse_records=prior,
            fewshots=[],
        )
    )
    assert any(r["fact_id"] == "f_walk_1" for r in brief["reuse_context"])
    # Eligibility unchanged — walk facts still in rater blocks.
    assert any("f_walk_1" in b.fact_ids for b in rater.blocks)


def test_fewshot_matching_no_cross_version_or_section() -> None:
    # Wrong structure version → empty
    assert (
        select_fewshots(
            structure_spec_id="test_alt_v1",
            section_key="current_status_history",
            block_keys=["family_history", "health_history"],
        )
        == []
    )
    # Wrong section → empty
    assert (
        select_fewshots(
            structure_spec_id="provisional_tj_v1",
            section_key="previous_evaluations",
            block_keys=["family_history"],
        )
        == []
    )
    matched = select_fewshots(
        structure_spec_id="provisional_tj_v1",
        section_key="current_status_history",
        block_keys=["family_history", "health_history"],
    )
    assert matched
    assert all(m.structure_spec_id == "provisional_tj_v1" for m in matched)
    assert all(m.section_key == "current_status_history" for m in matched)


def test_alternate_structure_changes_labels_without_code_branch() -> None:
    ledger = _mini_ledger()
    base = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    alt = compile_history_plan(ledger, structure_spec_id="test_alt_v1")
    base_csh = next(s for s in base.sections if s.section_key == "current_status_history")
    alt_csh = next(s for s in alt.sections if s.section_key == "current_status_history")
    assert [b.block_key for b in base_csh.blocks] != [b.block_key for b in alt_csh.blocks]
    assert [b.display_label for b in alt_csh.blocks][0] == "Medical Background"
    # Same compiler path — only the JSON changed.
    assert load_structure_spec("test_alt_v1")["structure_spec_id"] == "test_alt_v1"


def test_legacy_draft_helpers_still_work() -> None:
    ledger = _mini_ledger()
    assert section_has_supporting_facts(ledger, "history") is True
    empty = ledger.model_copy(update={"facts": []})
    assert section_has_supporting_facts(empty, "history") is False
    blocks = [
        DraftBlock(
            kind=DraftBlockKind.PROSE,
            label="Health History",
            trigger=None,
            prose="Jordan has a known peanut allergy.",
            statements=[
                DraftStatement(
                    statement="Peanut allergy.",
                    quote="known peanut allergy",
                    fact_ids=["f_allergy_1"],
                )
            ],
        )
    ]
    out = finalize_draft_output(DraftProseOutput(blocks=blocks, prose="", statements=[]), ledger)
    assert "Health History" in out.prose
    assert out.statements


def test_rendering_and_traceability_prose_and_table() -> None:
    prose_block = DraftBlock(
        kind=DraftBlockKind.PROSE,
        label="School Experience",
        trigger=None,
        prose="Jordan is in fourth grade.",
        statements=[
            DraftStatement(
                statement="Grade 4.",
                quote="fourth grade",
                fact_ids=["f_grade_1"],
            )
        ],
    )
    table_block = DraftBlock(
        kind=DraftBlockKind.TABLE,
        label="School History",
        trigger=None,
        table=DraftTable(
            title="School History",
            columns=["Year/Grade", "Attendance"],
            rows=[
                [
                    DraftCell(text="4", fact_ids=["f_grade_1"]),
                    DraftCell(text="", fact_ids=[]),
                ]
            ],
        ),
        statements=[],
    )
    rendered = render_prose_from_blocks([prose_block, table_block])
    assert "**School Experience:**" in rendered
    assert "**School History:**" in rendered
    assert "| 4 |" in rendered or "| 4 |" in rendered.replace(" ", "")
    assert "f_grade_1" in prose_block.statements[0].fact_ids
    assert table_block.table is not None
    assert table_block.table.rows[0][0].fact_ids == ["f_grade_1"]


def test_score_report_excluded_from_previous_evaluations() -> None:
    ledger = _mini_ledger()
    prior = select_previous_evaluations(ledger)
    ids = {f.id for f in prior.facts}
    assert "f_prior_1" in ids
    assert "f_score_1" not in ids
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    prev = next(s for s in plan.sections if s.section_key == "previous_evaluations")
    assert all(fid != "f_score_1" for b in prev.blocks for fid in b.fact_ids)


def test_case_brief_is_deterministic_json() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    a = case_brief_json(
        plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
    )
    b = case_brief_json(
        plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
    )
    assert a == b
    payload = json.loads(a)
    assert payload["structure_spec_id"] == "provisional_tj_v1"
    assert payload["section_key"] == "current_status_history"


def test_history_system_voice_rules_stripped_after_gate() -> None:
    """Stage C: Rule 5/6/7 are gone; few-shots + gate carry voice."""

    text = history_system_prompt("Current Status & History")
    assert "in the style demonstrated by the example" in text
    assert "Hard rules" in text
    assert "Name the source for second-hand claims" not in text
    assert "Labeled thematic blocks with complete connected prose" not in text
    assert "No absence filler, document narration, or meta-narration" not in text
    assert "Write about the child, not the paperwork" not in text
    lowered = text.lower()
    assert "records indicate" not in lowered
    assert "reports from various sources indicate" not in lowered
    # Reliability spine remains; ids are traced by code, not the drafting call.
    assert "Ledger only" in text
    assert "Do not put ledger ids" in text
    assert "Header owns DOB" in text
    assert "statements cover every substantive claim" not in text.lower()


def test_history_draft_messages_are_phase1_pairs_with_trace_brief() -> None:
    """Phase-1 excerpts are real user/assistant pairs; model-facing brief has no ids."""

    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    from history_compiler import model_facing_case_brief_json

    brief = model_facing_case_brief_json(
        plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
    )
    messages = build_history_draft_messages(
        section_display_label=section.display_label,
        section_key=section.section_key,
        user_brief=brief,
    )
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assert "Caleb Whitfield" in messages[2]["content"]
    assert "Pregnancy and Delivery" in messages[2]["content"]
    case_user = messages[3]["content"]
    assert "Caleb Whitfield" not in case_user
    assert "f_fam_1" not in case_user
    assert '"fact_id"' not in case_user
    assert '"fact_ids"' not in case_user
    assert "maternal ADHD" in case_user
    assert '"fewshots": []' in case_user or '"fewshots":[]' in case_user.replace(" ", "")
    # Policy no longer asks the model to self-align.
    assert "Do not put ledger ids" in messages[0]["content"]
    assert "Trace every substantive span" not in messages[0]["content"]


def test_compile_section_briefs_are_inspectable() -> None:
    ledger = _mini_ledger()
    compiled = compile_section_briefs(ledger, conflicts=[], variance=[])
    keys = [s["section_key"] for s in compiled["sections"]]
    assert "current_status_history" in keys
    family = next(s for s in compiled["sections"] if s["section_key"] == "current_status_history")
    assert family["populated"] is True
    assert family["fact_count"] >= 1
    assert "Family History" in family["markdown"]
    assert "f_fam_1" in family["markdown"] or "family_history" in family["markdown"]


def test_claim_and_source_wording_leads_with_normalized_claim() -> None:
    claim, source = claim_and_source_wording(
        "history of neglect, trauma suspected",
        "History of trauma (including abuse, neglect, molest, or domestic violence): "
        "Yes of neglect, trauma suspected.",
    )
    assert claim == "history of neglect, trauma suspected"
    assert source is not None
    assert source.startswith("History of trauma")
    assert "Yes of neglect" in source

    # Scaffolded spans stay available; claim does not replace them.
    claim, source = claim_and_source_wording(
        "Emma Rose Callahan",
        "Student Legal Name: Emma Rose Callahan",
    )
    assert claim == "Emma Rose Callahan"
    assert source == "Student Legal Name: Emma Rose Callahan"

    claim, source = claim_and_source_wording(
        "ridgeway high",
        "School of Attendance: Ridgeway High",
    )
    assert claim == "ridgeway high"
    assert source == "School of Attendance: Ridgeway High"

    claim, source = claim_and_source_wording(
        "cooperative",
        "Level of cooperation: cooperative, persisted, complained about hard things, "
        "but could laugh at herself",
    )
    assert claim == "cooperative"
    assert source is not None
    assert "persisted" in source

    # Empty claim falls back to the span alone.
    claim, source = claim_and_source_wording("", "walked at 18 months")
    assert claim == "walked at 18 months"
    assert source is None

    claim, source = claim_and_source_wording("walked at 18 months", "walked at 18 months")
    assert claim == "walked at 18 months"
    assert source is None


def test_evidence_brief_leads_with_claim_not_corrupted_span() -> None:
    """The drafting brief narrates the normalized claim; the span is labeled."""

    ledger = _mini_ledger()
    # Graft the fixture_001 family-history shape onto the mini ledger.
    ledger.facts[0] = ledger.facts[0].model_copy(
        update={
            "id": "f_doc_26_008",
            "value": "history of neglect, trauma suspected",
            "value_text": (
                "History of trauma (including abuse, neglect, molest, or domestic "
                "violence): Yes of neglect, trauma suspected."
            ),
        }
    )
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    md = render_evidence_brief_markdown(plan, section, ledger)
    primary = next(
        ln
        for ln in md.splitlines()
        if ln.startswith("- **family_history**")
        and "history of neglect, trauma suspected" in ln
    )
    assert "`f_doc_26_008`" not in primary
    assert "Yes of neglect" not in primary
    idx = md.splitlines().index(primary)
    source_line = md.splitlines()[idx + 1]
    assert source_line.startswith("  - source wording:")
    assert "Yes of neglect" in source_line

    payload = json.loads(
        case_brief_json(
            plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
        )
    )
    row = next(
        f
        for facts in payload["facts_by_block"].values()
        for f in facts
        if f["fact_id"] == "f_doc_26_008"
    )
    assert row["claim"] == "history of neglect, trauma suspected"
    assert "Yes of neglect" in row["source_wording"]
    # Raw ledger fields stay on the structured payload for code; they are not
    # the primary narratable line.
    assert "Yes of neglect" in row["value_text"]


def test_fixture_001_family_history_brief_leads_with_claim() -> None:
    """Cached parent stays corrupt; the brief is resilient without rewriting it."""

    cache = _DIR / "evals" / "cache" / "fixture_001_ledger.json"
    raw = json.loads(cache.read_text(encoding="utf-8"))
    ledger = Ledger.model_validate(raw["ledger"])
    fact = next(f for f in ledger.facts if f.id == "f_doc_26_008")
    assert fact.value == "history of neglect, trauma suspected"
    assert "Yes of neglect" in fact.value_text
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    md = render_evidence_brief_markdown(plan, section, ledger)
    primary = next(
        ln
        for ln in md.splitlines()
        if ln.startswith("- **family_history**")
        and "history of neglect, trauma suspected" in ln
    )
    assert primary == (
        "- **family_history** · history of neglect, trauma suspected"
    )
    assert "`f_doc_26_008`" not in primary
    source_line = md.splitlines()[md.splitlines().index(primary) + 1]
    assert source_line.startswith("  - source wording:")
    assert "Yes of neglect" in source_line
    lines = format_fact_evidence_lines(
        fact.predicate, fact.value, fact.value_text
    )
    assert lines[0] == primary
    assert "source wording" in lines[1]


def test_markdown_fact_bullets_omit_ledger_ids() -> None:
    """Stage C1: model-facing fact bullets keep claim-then-span, drop `{fid}`."""

    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    md = render_evidence_brief_markdown(plan, section, ledger)
    # Old shape: `- `f_fam_1` · **family_history** · …`
    assert not any(ln.startswith("- `") and "· **" in ln for ln in md.splitlines())
    bullet_lines = [ln for ln in md.splitlines() if ln.startswith("- **")]
    assert bullet_lines
    ledger_ids = {f.id for f in ledger.facts}
    for ln in bullet_lines:
        for fid in ledger_ids:
            assert fid not in ln, ln
    # Structured payload still carries ids for code / self-alignment.
    payload = json.loads(
        case_brief_json(
            plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
        )
    )
    family = payload["facts_by_block"]["family_history"]
    assert any(f["fact_id"] == "f_fam_1" for f in family)


def test_model_facing_brief_contains_no_ledger_id() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    from history_compiler import model_facing_case_brief_json

    facing = model_facing_case_brief_json(
        plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
    )
    for fact in ledger.facts:
        assert fact.id not in facing
    assert '"fact_id"' not in facing
    assert '"fact_ids"' not in facing
    code = case_brief_json(
        plan, section, ledger, conflicts=[], variance=[], reuse_records=[], fewshots=[]
    )
    assert "f_fam_1" in code


def test_aligner_writes_statements_from_prose_only_model() -> None:
    from history_draft import ModelDraftBlock, ModelDraftOutput, align_model_output_to_section
    from schemas import DraftBlockKind

    ledger = _mini_ledger()
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    model_output = ModelDraftOutput(
        blocks=[
            ModelDraftBlock(
                kind=DraftBlockKind.PROSE,
                label="Family History",
                prose="A maternal uncle has ADHD.",
            )
        ]
    )
    output = align_model_output_to_section(
        model_output, section, child_name=ledger.child.name
    )
    assert output.blocks[0].statements
    assert output.blocks[0].statements[0].fact_ids == ["f_fam_1"]
    assert "f_fam_1" not in (output.blocks[0].prose or "")


def test_table_na_cells_become_blank() -> None:
    from history_draft import ModelDraftCell, ModelDraftTable, _align_table

    ledger = _mini_ledger()
    grade = next(f for f in ledger.facts if f.id == "f_grade_1")
    table = ModelDraftTable(
        title="School History",
        columns=["Grade", "Notes"],
        rows=[[ModelDraftCell(text="4"), ModelDraftCell(text="N/A")]],
    )
    aligned = _align_table(table, [grade])
    assert aligned.rows[0][0].text == "4"
    assert aligned.rows[0][0].fact_ids == ["f_grade_1"]
    assert aligned.rows[0][1].text == ""
    assert aligned.rows[0][1].fact_ids == []


if __name__ == "__main__":
    tests = [
        test_structure_spec_validation_rejects_duplicates_and_bad_refs,
        test_provisional_tj_v1_compiles_exact_order,
        test_unsupported_blocks_absent_no_filler,
        test_raters_distinct_and_consolidate,
        test_topic_and_rater_may_select_same_fact,
        test_every_occurrence_keeps_fact_id,
        test_reuse_context_records_without_suppressing,
        test_fewshot_matching_no_cross_version_or_section,
        test_alternate_structure_changes_labels_without_code_branch,
        test_legacy_draft_helpers_still_work,
        test_rendering_and_traceability_prose_and_table,
        test_score_report_excluded_from_previous_evaluations,
        test_case_brief_is_deterministic_json,
        test_history_system_voice_rules_stripped_after_gate,
        test_history_draft_messages_are_phase1_pairs_with_trace_brief,
        test_compile_section_briefs_are_inspectable,
        test_claim_and_source_wording_leads_with_normalized_claim,
        test_evidence_brief_leads_with_claim_not_corrupted_span,
        test_fixture_001_family_history_brief_leads_with_claim,
        test_markdown_fact_bullets_omit_ledger_ids,
        test_model_facing_brief_contains_no_ledger_id,
        test_aligner_writes_statements_from_prose_only_model,
        test_table_na_cells_become_blank,
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
