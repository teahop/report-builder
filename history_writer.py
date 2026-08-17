"""Positive History prose writer — diagnostic eval helper, not a production lane.

Production drafting is history_draft.py (thin prompt + phase-1 few-shots +
DraftProseOutput). This module keeps the prose-only diagnostic schema for
historical ladder/sweep runners.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from history_compiler import (
    PlannedSection,
    claim_and_source_wording,
    compile_history_plan,
)
from history_fewshots import load_phase1_registry, select_phase1_example
from history_schemas import FactReuseRecord
from schemas import Disagreement, Ledger

_DIR = Path(__file__).resolve().parent
WRITER_PROMPT_PATH = _DIR / "history_writer_prompt.md"
TABLE_POSITION_MARKER = (
    "[SCHOOL HISTORY CHART — server-owned; do not generate cells]"
)
TRACE_ALIGNMENT_STATUS = "not_run_diagnostic"
DIAGNOSTIC_BANNER = (
    "DIAGNOSTIC ONLY — UPSTREAM EXTRACTION/LEDGER NOT ACCEPTED"
)


class WriterProseBlock(BaseModel):
    """Prose-only block. No fact_ids or trace statements."""

    label: str
    prose: str = ""
    table_position: bool = False


class WriterSectionOutput(BaseModel):
    blocks: list[WriterProseBlock] = Field(default_factory=list)


def writer_prompt_template() -> str:
    return WRITER_PROMPT_PATH.read_text(encoding="utf-8").strip() + "\n"


def stable_writer_instruction(section_display_label: str) -> str:
    """Exact product-approved text after substituting the section label."""

    return writer_prompt_template().format(
        section_display_label=section_display_label
    )


def writer_prompt_hash(section_display_label: str) -> str:
    return hashlib.sha256(
        stable_writer_instruction(section_display_label).encode("utf-8")
    ).hexdigest()


def _disagreement_fact_ids(item: Disagreement) -> set[str]:
    return {v.fact_id for v in item.versions}


def _version_brief_text(version: object) -> str:
    claim, source = claim_and_source_wording(
        getattr(version, "value", None),
        getattr(version, "value_text", None),
    )
    if source:
        return f'{claim} (source wording: "{source}")'
    return claim


def _conflict_note(item: Disagreement) -> dict[str, str]:
    return {
        "topic": item.topic,
        "text": "; ".join(_version_brief_text(v) for v in item.versions),
    }


def concise_writer_brief(
    section: PlannedSection,
    ledger: Ledger,
    *,
    conflicts: list[Disagreement],
    variance: list[Disagreement],
    reuse_records: list[FactReuseRecord],
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """One narrative item per fact. No fact_ids, timelines, or example JSON."""

    offered: dict[str, list[str]] = {}
    plan: list[dict[str, str]] = []
    evidence: list[dict[str, str]] = []
    seen: set[str] = set()
    sources = {s.id: s for s in ledger.sources}

    for block in section.blocks:
        offered[block.block_key] = list(block.fact_ids)
        if block.kind == "table":
            plan.append(
                {
                    "label": block.display_label,
                    "kind": "table_position",
                    "marker": TABLE_POSITION_MARKER,
                }
            )
            continue
        plan.append({"label": block.display_label, "kind": "prose"})
        for fact in block.facts:
            if fact.id in seen:
                continue
            seen.add(fact.id)
            claim, source_wording = claim_and_source_wording(
                fact.value, fact.value_text
            )
            item: dict[str, str] = {
                "topic": block.display_label,
                "text": claim,
            }
            if source_wording:
                item["source_wording"] = source_wording
            if fact.reporter:
                item["who"] = str(fact.reporter)
            source = sources.get(fact.source_id)
            if source is not None:
                item["source"] = source.label
                if source.date:
                    item["when"] = source.date
            elif fact.source_date:
                item["when"] = fact.source_date
            evidence.append(item)

    section_ids = {fid for ids in offered.values() for fid in ids}
    payload: dict[str, Any] = {
        "section_label": section.display_label,
        "student_name": ledger.child.name,
        "section_plan": plan,
        "evidence": evidence,
    }
    must = [
        _conflict_note(c)
        for c in conflicts
        if section_ids.intersection(_disagreement_fact_ids(c))
    ]
    if must:
        payload["must_mention"] = must
    var = [
        _conflict_note(v)
        for v in variance
        if section_ids.intersection(_disagreement_fact_ids(v))
    ]
    if var:
        payload["comparisons"] = var
    reuse_notes = []
    for rec in reuse_records:
        if rec.fact_id not in section_ids:
            continue
        reuse_notes.append(
            "This section should present this evidence again for "
            f"{section.purpose}; it already appeared in "
            f"{rec.section_key}/{rec.block_key} as {rec.purpose}."
        )
    if reuse_notes:
        payload["reuse_notes"] = reuse_notes
    return payload, offered


def format_writer_user(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def example_user_message(example: dict[str, Any]) -> str:
    user = example["example_user"]
    payload = {
        "section_label": user.get("section_label") or example.get("display_label"),
        "section_plan": user.get("section_plan") or [],
        "evidence": user.get("evidence") or {},
    }
    return format_writer_user(payload)


def build_writer_messages(
    *,
    section_display_label: str,
    example: dict[str, Any],
    case_payload: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": stable_writer_instruction(section_display_label)},
        {"role": "user", "content": example_user_message(example)},
        {"role": "assistant", "content": example["example_text"]},
        {"role": "user", "content": format_writer_user(case_payload)},
    ]


def attach_plan_identity(
    output: WriterSectionOutput,
    section: PlannedSection,
    offered: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Emit planned blocks in server order; fill from matching writer labels."""

    by_label: dict[str, WriterProseBlock] = {}
    unused: list[WriterProseBlock] = []
    for model_block in output.blocks:
        if model_block.label not in by_label:
            by_label[model_block.label] = model_block
        else:
            unused.append(model_block)

    attached: list[dict[str, Any]] = []
    for plan_block in section.blocks:
        is_table = plan_block.kind == "table"
        model_block = by_label.pop(plan_block.display_label, None)
        if model_block is None and unused:
            model_block = unused.pop(0)
        if is_table:
            prose = TABLE_POSITION_MARKER
            kind = "table_position"
        elif model_block is not None:
            prose = TABLE_POSITION_MARKER if model_block.table_position else (
                model_block.prose or ""
            )
            kind = "table_position" if model_block.table_position else "prose"
        else:
            prose = ""
            kind = "prose"
        row: dict[str, Any] = {
            "block_key": plan_block.block_key,
            "display_label": plan_block.display_label,
            "kind": kind,
            "prose": prose,
            "offered_evidence_ids": list(offered.get(plan_block.block_key) or []),
        }
        if not is_table and not prose:
            row["missing_from_writer"] = True
        attached.append(row)
    return attached


def render_diagnostic_section(display_label: str, blocks: list[dict[str, Any]]) -> str:
    parts = [f"## {display_label}", ""]
    for block in blocks:
        parts.append(f"**{block['display_label']}:**")
        parts.append(block.get("prose") or "")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def messages_hash(messages: list[dict[str, str]]) -> str:
    blob = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compile_writer_section_request(
    section: PlannedSection,
    ledger: Ledger,
    *,
    conflicts: list[Disagreement],
    variance: list[Disagreement],
    reuse_records: list[FactReuseRecord],
) -> dict[str, Any]:
    example = select_phase1_example(section.section_key)
    case_payload, offered = concise_writer_brief(
        section,
        ledger,
        conflicts=conflicts,
        variance=variance,
        reuse_records=reuse_records,
    )
    messages = build_writer_messages(
        section_display_label=section.display_label,
        example=example,
        case_payload=case_payload,
    )
    return {
        "section_key": section.section_key,
        "display_label": section.display_label,
        "purpose": section.purpose,
        "example_id": example["example_id"],
        "example_text_sha256": example["example_text_sha256"],
        "evidence_brief_sha256": example["evidence_brief_sha256"],
        "approved_case_id": example["approved_case_id"],
        "known_weakness": example.get("known_weakness"),
        "writer_prompt_hash": writer_prompt_hash(section.display_label),
        "messages": messages,
        "messages_sha256": messages_hash(messages),
        "case_payload": case_payload,
        "offered_evidence_ids": offered,
        "trace_alignment_status": TRACE_ALIGNMENT_STATUS,
    }


def plan_writer_calls(
    ledger: Ledger,
    *,
    structure_spec_id: str = "provisional_tj_v1",
    conflicts: list[Disagreement] | None = None,
    variance: list[Disagreement] | None = None,
) -> tuple[Any, list[dict[str, Any]]]:
    plan = compile_history_plan(ledger, structure_spec_id=structure_spec_id)
    reuse: list[FactReuseRecord] = []
    requests: list[dict[str, Any]] = []
    for section in plan.sections:
        if not section.blocks:
            continue
        req = compile_writer_section_request(
            section,
            ledger,
            conflicts=conflicts or [],
            variance=variance or [],
            reuse_records=reuse,
        )
        requests.append(req)
        for block_key, ids in req["offered_evidence_ids"].items():
            for fid in ids:
                reuse.append(
                    FactReuseRecord(
                        fact_id=fid,
                        section_key=section.section_key,
                        block_key=block_key,
                        purpose=section.purpose,
                    )
                )
    return plan, requests
