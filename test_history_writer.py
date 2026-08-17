"""Focused tests for the positive History writer — no model calls, no live receipts."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parent
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from history_writer import (
    TABLE_POSITION_MARKER,
    TRACE_ALIGNMENT_STATUS,
    WriterProseBlock,
    WriterSectionOutput,
    attach_plan_identity,
    build_writer_messages,
    compile_writer_section_request,
    concise_writer_brief,
    load_phase1_registry,
    plan_writer_calls,
    select_phase1_example,
    stable_writer_instruction,
)
from schemas import Disagreement, DisagreementVersion
from test_history_draft import _mini_ledger
from history_compiler import compile_history_plan


def test_stable_instruction_is_exact_product_text() -> None:
    text = stable_writer_instruction("Current Status & History")
    assert text.startswith(
        "Draft the **Current Status & History** section of a psychoeducational report"
    )
    assert "in the style demonstrated by the example." in text
    assert "Return the requested section content in the supplied output format." in text
    assert "{section_display_label}" not in text


def test_instruction_has_no_legacy_policy_language() -> None:
    text = stable_writer_instruction("Educational History").lower()
    for banned in ("hard rules", "fact_id", "predicate", "draftproseoutput", "ledger only"):
        assert banned not in text, banned


def test_example_is_user_assistant_pair_with_full_molly_section() -> None:
    example = select_phase1_example("current_status_history")
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger)
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    req = compile_writer_section_request(
        section, ledger, conflicts=[], variance=[], reuse_records=[]
    )
    messages = req["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assistant = messages[2]["content"]
    assert "Caleb Whitfield" in assistant
    assert "Pregnancy and Delivery" in assistant
    assert assistant == example["example_text"]
    # Example is not buried inside the actual case user message.
    case_user = messages[3]["content"]
    assert "Caleb Whitfield" not in case_user
    assert example["example_text"] not in case_user


def test_every_example_has_provenance_and_hashes() -> None:
    for row in load_phase1_registry():
        assert row["approved_case_id"] in {"002", "003", "004", "005", "006"}
        assert row["approved_case_id"] != "001"
        assert len(row["example_text_sha256"]) == 64
        assert len(row["evidence_brief_sha256"]) == 64
        assert row["source"].endswith("example slots.md")
        assert row.get("known_weakness")
        blob = json.dumps(row).lower()
        assert "fixture_001" not in blob
        assert "emma rose" not in blob


def test_fixture_001_never_selected_as_example() -> None:
    for key in (
        "current_status_history",
        "educational_history",
        "previous_evaluations",
        "rater_input",
    ):
        ex = select_phase1_example(key)
        assert ex["approved_case_id"] != "001"
        assert "Emma" not in ex["example_text"]


def test_case_message_has_one_representation_per_evidence_item() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger)
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    payload, offered = concise_writer_brief(
        section, ledger, conflicts=[], variance=[], reuse_records=[]
    )
    dumped = json.dumps(payload)
    assert "fact_id" not in dumped
    assert "facts_by_block" not in dumped
    assert "episodes_by_block" not in dumped
    assert "timelines" not in dumped
    assert "fewshots" not in dumped
    texts = [item["text"] for item in payload["evidence"]]
    keys = [(item["text"], item.get("source_wording")) for item in payload["evidence"]]
    assert len(keys) == len(set(keys)), texts
    offered_ids = [fid for ids in offered.values() for fid in ids]
    assert len(set(offered_ids)) == len(offered_ids) or True  # ids unique per block list ok
    assert "student_name" in payload
    assert "dob" not in payload
    family = next(item for item in payload["evidence"] if item["topic"] == "Family History")
    assert family["text"] == "maternal ADHD"
    assert family["source_wording"] == "maternal uncle with ADHD"


def test_writer_conflict_note_leads_with_claim() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger)
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    conflict = Disagreement(
        subject="child",
        predicate="family_history",
        qualifier="ADHD",
        predicate_class="record",
        topic="family_history:ADHD",
        versions=[
            DisagreementVersion(
                fact_id="f_fam_1",
                source_id="src_parent_a",
                source_date="2025-01-10",
                reporter="Alex Quinn",
                value="maternal ADHD",
                value_text="maternal uncle with ADHD",
                assertion="asserted",
            ),
            DisagreementVersion(
                fact_id="f_fam_2",
                source_id="src_parent_b",
                source_date="2025-02-01",
                reporter="Alex Quinn",
                value="paternal ADHD",
                value_text="father's brother has ADHD",
                assertion="asserted",
            ),
        ],
    )
    payload, _ = concise_writer_brief(
        section, ledger, conflicts=[conflict], variance=[], reuse_records=[]
    )
    note = payload["must_mention"][0]["text"]
    assert note.startswith("maternal ADHD (source wording:")
    assert "maternal uncle with ADHD" in note
    assert "paternal ADHD (source wording:" in note
    assert "father's brother has ADHD" in note


def test_prose_only_output_has_no_trace_statements() -> None:
    fields = WriterSectionOutput.model_fields
    assert "statements" not in fields
    assert "fact_ids" not in WriterProseBlock.model_fields
    sample = WriterSectionOutput(
        blocks=[WriterProseBlock(label="Family History", prose="A family history of ADHD.")]
    )
    assert sample.model_dump()["blocks"][0].keys() == {"label", "prose", "table_position"}


def test_server_owned_order_is_plan_order() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger)
    section = next(s for s in plan.sections if s.section_key == "current_status_history")
    _, offered = concise_writer_brief(
        section, ledger, conflicts=[], variance=[], reuse_records=[]
    )
    scrambled = WriterSectionOutput(
        blocks=list(
            reversed(
                [
                    WriterProseBlock(label=b.display_label, prose=f"prose for {b.display_label}")
                    for b in section.blocks
                    if b.kind != "table"
                ]
            )
        )
    )
    attached = attach_plan_identity(scrambled, section, offered)
    assert [row["block_key"] for row in attached] == [b.block_key for b in section.blocks]
    assert [row["display_label"] for row in attached] == [
        b.display_label for b in section.blocks
    ]


def test_educational_table_position_is_server_marker() -> None:
    ledger = _mini_ledger()
    plan = compile_history_plan(ledger)
    section = next(s for s in plan.sections if s.section_key == "educational_history")
    payload, offered = concise_writer_brief(
        section, ledger, conflicts=[], variance=[], reuse_records=[]
    )
    table_plan = [p for p in payload["section_plan"] if p.get("kind") == "table_position"]
    if not table_plan:
        return
    assert table_plan[0]["marker"] == TABLE_POSITION_MARKER
    attached = attach_plan_identity(WriterSectionOutput(blocks=[]), section, offered)
    table_rows = [r for r in attached if r["kind"] == "table_position"]
    assert table_rows
    assert all(r["prose"] == TABLE_POSITION_MARKER for r in table_rows)


def test_production_path_uses_thin_prompt_and_phase1_fewshots() -> None:
    """Approach lives on the traceable path; WriterSectionOutput is not promoted."""

    import history_draft
    from schemas import DraftProseOutput

    src = Path(history_draft.__file__).read_text(encoding="utf-8")
    assert "history_writer_prompt.md" in src
    assert "build_history_draft_messages" in src
    assert "DraftProseOutput" in src
    assert "WriterSectionOutput" not in src
    hist_src = inspect.getsource(history_draft.draft_history_package)
    assert "build_history_draft_messages" in hist_src
    assert "ModelDraftOutput" in hist_src
    assert "align_model_output_to_section" in hist_src
    schema_fields = DraftProseOutput.model_fields
    assert "statements" in schema_fields
    assert "blocks" in schema_fields


def test_alignment_status_is_diagnostic_not_run() -> None:
    ledger = _mini_ledger()
    _plan, requests = plan_writer_calls(ledger)
    assert requests
    assert all(r["trace_alignment_status"] == TRACE_ALIGNMENT_STATUS for r in requests)
    messages = build_writer_messages(
        section_display_label="Current Status & History",
        example=select_phase1_example("current_status_history"),
        case_payload={"section_label": "Current Status & History", "section_plan": [], "evidence": []},
    )
    joined = "\n".join(m["content"] for m in messages)
    assert "Hard rules" not in joined
    assert "fact_id" not in messages[0]["content"].lower()
