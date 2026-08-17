"""History package orchestration — one model call per populated top-level section.

Production path for POST /draft/history. Voice is taught by the thin product prompt
plus phase-1 approved-excerpt few-shots; reliability stays on DraftProseOutput
(fact_ids / statements / must-mention / terminology / temporal / entailment).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import re
from typing import Self

from pydantic import BaseModel, Field, model_validator

from draft_output import (
    finalize_draft_output,
    output_to_report_section,
    render_annotated_review,
)
from draft_validators import (
    build_citation_review_items,
    build_conflict_review_items,
    build_variance_review_items,
    validate_conflicts_mentioned,
    validate_draft_blocks,
    validate_entailment,
    validate_fact_id_trace,
    validate_temporal_framing,
    validate_terminology_flags,
    review_items_from_visible_fact_ids,
)
from history_align import align_prose_to_facts, match_fact_to_span
from history_compiler import (
    PlannedSection,
    compile_history_plan,
    model_facing_case_brief_json,
)
from history_fewshots import format_phase1_user_message, select_phase1_example
from history_langfuse import attach_langfuse_ids, update_history_trace_metadata
from history_schemas import (
    DraftedBlock,
    DraftedSection,
    FactReuseRecord,
    HistoryDraftPackage,
    HistoryDraftRequest,
    HistoryDraftResponse,
)
from history_structure import structure_spec_hash
from langfuse import observe
from provider import DRAFT_TEMPERATURE, ModelProvider, compute_cost_usd
from schemas import (
    DraftBlock,
    DraftBlockKind,
    DraftCell,
    DraftProseOutput,
    DraftResponse,
    DraftTable,
    Fact,
    ReviewItem,
    ReviewQueue,
)
from validators import validate_age_consistency
from voice_store import (
    evaluate_voice_gates,
    merge_voice_reports,
    review_items_from_gate,
    voice_store_sha,
)

_DIR = Path(__file__).resolve().parent
HISTORY_POLICY = (_DIR / "history_policy.md").read_text(encoding="utf-8")
WRITER_PROMPT_TEMPLATE = (_DIR / "history_writer_prompt.md").read_text(encoding="utf-8")


class ModelDraftCell(BaseModel):
    """Table cell as authored by the model — text only; server attaches fact_ids."""

    text: str = Field(
        description='Cell text. Use "" for a blank cell — never "N/A", never filler.',
    )


class ModelDraftTable(BaseModel):
    title: str
    columns: list[str] = Field(min_length=1)
    rows: list[list[ModelDraftCell]] = Field(default_factory=list)


class ModelDraftBlock(BaseModel):
    """Prose-only block. No statements or fact_ids — the server traces after."""

    kind: DraftBlockKind
    label: str = Field(description="Bold run-in label for this block")
    trigger: str | None = None
    prose: str | None = None
    table: ModelDraftTable | None = None

    @model_validator(mode="after")
    def _kind_payload(self) -> Self:
        if self.kind == DraftBlockKind.PROSE:
            if self.prose is None:
                raise ValueError("prose block requires prose")
            if self.table is not None:
                raise ValueError("prose block must not carry table")
        elif self.kind == DraftBlockKind.TABLE:
            if self.table is None:
                raise ValueError("table block requires table")
            if self.prose is not None:
                raise ValueError("table block must not carry prose")
        return self


class ModelDraftOutput(BaseModel):
    """Drafting-call schema: labeled blocks only. Server writes statements."""

    blocks: list[ModelDraftBlock] = Field(default_factory=list)


def history_policy_hash() -> str:
    return hashlib.sha256(HISTORY_POLICY.encode("utf-8")).hexdigest()


def stable_writer_instruction(section_display_label: str) -> str:
    """Exact product-approved thin prompt after substituting the section label."""

    return WRITER_PROMPT_TEMPLATE.strip().format(
        section_display_label=section_display_label
    ) + "\n"


def history_system_prompt(section_display_label: str) -> str:
    """Thin positive instruction plus reliability policy. Voice is few-shots + gate."""

    return (
        stable_writer_instruction(section_display_label).rstrip()
        + "\n\n"
        + HISTORY_POLICY.strip()
        + "\n"
    )


def prompt_hash_for_section(system: str, user: str) -> str:
    return hashlib.sha256(f"{system}\n---\n{user}".encode("utf-8")).hexdigest()


def prompt_hash_for_messages(messages: list[dict[str, str]]) -> str:
    blob = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_history_draft_messages(
    *,
    section_display_label: str,
    section_key: str,
    user_brief: str,
) -> list[dict[str, str]]:
    """System (thin prompt + policy) + phase-1 example pair + case brief."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": history_system_prompt(section_display_label)},
    ]
    try:
        example = select_phase1_example(section_key)
    except ValueError:
        example = None
    if example is not None:
        messages.append(
            {"role": "user", "content": format_phase1_user_message(example)}
        )
        messages.append({"role": "assistant", "content": example["example_text"]})
    messages.append({"role": "user", "content": user_brief})
    return messages


_FILLER_CELL = frozenset({"n/a", "na", "n.a."})
_CELL_TOKEN = re.compile(r"[a-z0-9]{4,}")


def _dedupe_ids(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for fid in ids:
        if fid not in seen:
            seen.add(fid)
            out.append(fid)
    return out


def _normalize_cell_text(text: str) -> str:
    stripped = text.strip()
    if stripped.lower() in _FILLER_CELL:
        return ""
    return text


def _cell_fact_ids(text: str, facts: list[Fact]) -> list[str]:
    """Content-match a table cell. Missing id beats a wrong one."""

    stripped = text.strip()
    if not stripped:
        return []
    matched = [fact.id for fact in facts if match_fact_to_span(fact, stripped)]
    if matched:
        return _dedupe_ids(matched)
    lowered = stripped.lower()
    cell_tokens = set(_CELL_TOKEN.findall(lowered))
    loose: list[str] = []
    for fact in facts:
        value = (fact.value or "").strip().lower()
        span = (fact.value_text or "").strip().lower()
        if value and value in lowered:
            loose.append(fact.id)
            continue
        if span and (span in lowered or lowered in span):
            loose.append(fact.id)
            continue
        fact_tokens = set(_CELL_TOKEN.findall(f"{value} {span}"))
        if cell_tokens and fact_tokens & cell_tokens:
            loose.append(fact.id)
    return _dedupe_ids(loose)


def _align_table(table: ModelDraftTable, facts: list[Fact]) -> DraftTable:
    rows: list[list[DraftCell]] = []
    for row in table.rows:
        cells: list[DraftCell] = []
        for cell in row:
            text = _normalize_cell_text(cell.text)
            ids = _cell_fact_ids(text, facts)
            if text.strip() and not ids:
                # Unmatched non-empty cell: blank rather than invent an id or 502.
                cells.append(DraftCell(text="", fact_ids=[]))
            else:
                cells.append(DraftCell(text=text, fact_ids=ids))
        rows.append(cells)
    return DraftTable(title=table.title, columns=list(table.columns), rows=rows)


def align_model_output_to_section(
    model_output: ModelDraftOutput,
    section: PlannedSection,
    *,
    child_name: str | None,
) -> DraftProseOutput:
    """Turn prose-only model blocks into DraftProseOutput with code-written statements."""

    planned = list(section.blocks)
    by_label = {b.display_label: b for b in planned}
    used: set[str] = set()
    blocks: list[DraftBlock] = []

    for model_block in model_output.blocks:
        plan_block = by_label.get(model_block.label)
        if plan_block is None or plan_block.block_key in used:
            plan_block = next((b for b in planned if b.block_key not in used), None)
        if plan_block is None:
            continue
        used.add(plan_block.block_key)
        facts = list(plan_block.facts)
        if model_block.kind == DraftBlockKind.TABLE:
            if model_block.table is None:
                continue
            blocks.append(
                DraftBlock(
                    kind=DraftBlockKind.TABLE,
                    label=plan_block.display_label,
                    trigger=model_block.trigger,
                    table=_align_table(model_block.table, facts),
                    statements=[],
                )
            )
            continue
        prose = model_block.prose or ""
        statements = align_prose_to_facts(
            prose, facts, exclude_name=child_name
        )
        blocks.append(
            DraftBlock(
                kind=DraftBlockKind.PROSE,
                label=plan_block.display_label,
                trigger=model_block.trigger,
                prose=prose,
                statements=statements,
            )
        )
    return DraftProseOutput(blocks=blocks, prose="", statements=[])


def _attach_plan_identity(
    output: DraftProseOutput,
    section: PlannedSection,
) -> list[DraftedBlock]:
    """
    Map model blocks onto planned block keys/labels.

    Structural identity comes from the plan. Match by exact display label first,
    then by order among remaining planned blocks.
    """

    planned = list(section.blocks)
    by_label = {b.display_label: b for b in planned}
    used: set[str] = set()
    drafted: list[DraftedBlock] = []

    for model_block in output.blocks:
        plan_block = by_label.get(model_block.label)
        if plan_block is None or plan_block.block_key in used:
            plan_block = next((b for b in planned if b.block_key not in used), None)
        if plan_block is None:
            continue
        used.add(plan_block.block_key)
        # Force server-owned label; keep model prose/table/statements.
        aligned = model_block.model_copy(update={"label": plan_block.display_label})
        fact_ids: list[str] = []
        for stmt in aligned.statements:
            fact_ids.extend(stmt.fact_ids)
        if aligned.kind == DraftBlockKind.TABLE and aligned.table is not None:
            for row in aligned.table.rows:
                for cell in row:
                    fact_ids.extend(cell.fact_ids)
        # De-dupe preserving order.
        seen: set[str] = set()
        ordered_ids: list[str] = []
        for fid in fact_ids:
            if fid not in seen:
                seen.add(fid)
                ordered_ids.append(fid)
        drafted.append(
            DraftedBlock(
                block_key=plan_block.block_key,
                display_label=plan_block.display_label,
                kind="table" if aligned.kind == DraftBlockKind.TABLE else "prose",
                draft_block=aligned,
                fact_ids=ordered_ids or list(plan_block.fact_ids),
            )
        )
    return drafted


def _records_from_drafted(
    section_key: str,
    purpose: str,
    drafted_blocks: list[DraftedBlock],
) -> list[FactReuseRecord]:
    records: list[FactReuseRecord] = []
    for block in drafted_blocks:
        for fid in block.fact_ids:
            records.append(
                FactReuseRecord(
                    fact_id=fid,
                    section_key=section_key,
                    block_key=block.block_key,
                    purpose=purpose,
                )
            )
    return records


def _finalize_section_response(
    provider: ModelProvider,
    *,
    output: DraftProseOutput,
    body: HistoryDraftRequest,
    model: str,
    entailment_model: str,
    draft_prompt_tokens: int,
    draft_completion_tokens: int,
    draft_total_tokens: int,
    section_key: str | None = None,
    voice_reports: list | None = None,
) -> DraftResponse:
    """Reuse legacy draft validation / review path for one section call."""

    tokens_by_stage: dict[str, int] = {"draft": draft_total_tokens, "entailment": 0}
    block_errors = validate_draft_blocks(output, body.ledger)
    if block_errors:
        raise ValueError("Draft block validation failed: " + "; ".join(block_errors[:5]))

    output = finalize_draft_output(output, body.ledger)

    trace_errors, failed_citations = validate_fact_id_trace(output, body.ledger)
    hard = [e for e in trace_errors if "statements list is empty" in e]
    if hard:
        raise ValueError("Draft fact_id trace failed: " + "; ".join(hard[:5]))

    if failed_citations:
        by_id = {f.id: f for f in body.ledger.facts}

        def _known_only(stmt):
            known = [fid for fid in stmt.fact_ids if fid in by_id]
            if not known:
                return None
            if known == list(stmt.fact_ids):
                return stmt
            return stmt.model_copy(update={"fact_ids": known})

        kept = [s for s in (_known_only(s) for s in output.statements) if s is not None]
        output = output.model_copy(update={"statements": kept})
        if not output.statements and output.prose.strip():
            raise ValueError(
                "Draft fact_id trace failed: all statements cited unknown fact_ids; "
                + "; ".join(trace_errors[:3])
            )

    section = output_to_report_section(
        output,
        section="history",
        ledger=body.ledger,
        conflicts=body.conflicts,
    )

    expected_age = validate_age_consistency(
        section,
        dob=body.ledger.child.dob,
        evaluation_date=body.ledger.child.evaluation_date,
        ledger=body.ledger,
    )

    review_items: list[ReviewItem] = []
    review_items.extend(build_conflict_review_items(body.conflicts))
    review_items.extend(build_variance_review_items(body.variance))
    review_items.extend(validate_conflicts_mentioned(output.prose, body.conflicts))
    review_items.extend(validate_terminology_flags(output.prose))
    review_items.extend(
        validate_temporal_framing(
            output,
            body.ledger,
            evaluation_date=body.ledger.child.evaluation_date,
            stale_as_of_days=body.stale_as_of_days,
        )
    )
    review_items.extend(build_citation_review_items(output.unverified_citations))
    review_items.extend(review_items_from_visible_fact_ids(output, body.ledger))
    voice_report = evaluate_voice_gates(
        output, ledger=body.ledger, section_key=section_key
    )
    review_items.extend(review_items_from_gate(voice_report))
    if voice_reports is not None:
        voice_reports.append(voice_report)

    e_prompt = e_completion = 0
    if not body.skip_entailment:
        entail_items, e_total, e_prompt, e_completion = validate_entailment(
            provider,
            model=entailment_model,
            output=output,
            ledger=body.ledger,
        )
        review_items.extend(entail_items)
        tokens_by_stage["entailment"] = e_total

    tokens_used = tokens_by_stage["draft"] + tokens_by_stage["entailment"]
    cost_usd = compute_cost_usd(
        model, draft_prompt_tokens, draft_completion_tokens
    ) + compute_cost_usd(entailment_model, e_prompt, e_completion)

    annotated_prose, unanchored_quotes = render_annotated_review(output)

    return DraftResponse(
        section_populated=True,
        empty_reason=None,
        answer=section,
        review=ReviewQueue(items=review_items),
        unverified_citations=list(output.unverified_citations),
        failed_citation_attempts=failed_citations,
        annotated_prose=annotated_prose,
        unanchored_quotes=unanchored_quotes,
        tokens_used=tokens_used,
        tokens_by_stage=tokens_by_stage,
        model=model,
        latency_ms=0,
        cost_usd=round(cost_usd, 6),
        age_years_expected=expected_age,
    )


@observe(name="stage.draft_history_package")
def draft_history_package(
    provider: ModelProvider,
    body: HistoryDraftRequest,
) -> HistoryDraftResponse:
    """
    Compile provisional structure → one DraftProseOutput call per populated
    section → assemble HistoryDraftPackage.

    Langfuse: this observe span is the parent; langfuse.openai generations from
    ModelProvider nest under it when LANGFUSE_* keys are set.
    """

    model = body.model or "gpt-4o-mini"
    entailment_model = body.entailment_model or "gpt-4o-mini"
    spec_hash = structure_spec_hash(body.structure_spec_id)
    policy_hash = history_policy_hash()
    store_sha = voice_store_sha()
    update_history_trace_metadata(
        structure_spec_id=body.structure_spec_id,
        structure_spec_hash=spec_hash,
        policy_hash=policy_hash,
        voice_store_sha=store_sha,
        model=model,
        skip_entailment=body.skip_entailment,
    )

    plan = compile_history_plan(body.ledger, structure_spec_id=body.structure_spec_id)
    reuse_records: list[FactReuseRecord] = []
    drafted_sections: list[DraftedSection] = []
    all_review: list[ReviewItem] = []
    tokens_by_stage: dict[str, int] = {"draft": 0, "entailment": 0}
    tokens_used = 0
    cost_usd = 0.0
    prompt_hashes: list[str] = []
    rendered_parts: list[str] = []
    voice_reports: list = []

    for section in plan.sections:
        if not section.blocks:
            drafted_sections.append(
                DraftedSection(
                    section_key=section.section_key,
                    display_label=section.display_label,
                    purpose=section.purpose,
                    blocks=[],
                    section_populated=False,
                    empty_reason=(
                        f"Section {section.section_key!r} offered in outline but "
                        "no supporting blocks resolved — no filler emitted."
                    ),
                )
            )
            continue

        user = model_facing_case_brief_json(
            plan,
            section,
            body.ledger,
            conflicts=body.conflicts,
            variance=body.variance,
            reuse_records=reuse_records,
            fewshots=[],
        )
        messages = build_history_draft_messages(
            section_display_label=section.display_label,
            section_key=section.section_key,
            user_brief=user,
        )
        section_prompt_hash = prompt_hash_for_messages(messages)
        prompt_hashes.append(section_prompt_hash)
        update_history_trace_metadata(
            **{
                f"section.{section.section_key}.prompt_hash": section_prompt_hash,
                f"section.{section.section_key}.block_keys": [
                    b.block_key for b in section.blocks
                ],
            }
        )

        result = provider.complete_structured(
            model=model,
            messages=messages,
            schema=ModelDraftOutput,
            temperature=DRAFT_TEMPERATURE,
        )
        model_output = result.data
        assert isinstance(model_output, ModelDraftOutput)
        output = align_model_output_to_section(
            model_output,
            section,
            child_name=body.ledger.child.name,
        )

        legacy = _finalize_section_response(
            provider,
            output=output,
            body=body,
            model=model,
            entailment_model=entailment_model,
            draft_prompt_tokens=result.prompt_tokens,
            draft_completion_tokens=result.completion_tokens,
            draft_total_tokens=result.total_tokens,
            section_key=section.section_key,
            voice_reports=voice_reports,
        )
        finalized = finalize_draft_output(output, body.ledger)
        drafted_blocks = _attach_plan_identity(finalized, section)
        package_blocks = [db.draft_block for db in drafted_blocks]
        package_output = finalize_draft_output(
            DraftProseOutput(blocks=package_blocks, prose="", statements=[]),
            body.ledger,
        )

        drafted_sections.append(
            DraftedSection(
                section_key=section.section_key,
                display_label=section.display_label,
                purpose=section.purpose,
                blocks=drafted_blocks,
                draft_output=package_output,
                section_populated=True,
                empty_reason=None,
                legacy_draft=legacy,
            )
        )
        rendered_parts.append(
            f"## {section.display_label}\n\n{package_output.prose}".rstrip()
        )
        reuse_records.extend(
            _records_from_drafted(section.section_key, section.purpose, drafted_blocks)
        )
        all_review.extend(legacy.review.items)
        tokens_used += legacy.tokens_used
        cost_usd += legacy.cost_usd
        for k, v in legacy.tokens_by_stage.items():
            tokens_by_stage[k] = tokens_by_stage.get(k, 0) + v

    package = HistoryDraftPackage(
        structure_spec_id=body.structure_spec_id,
        structure_spec_hash=spec_hash,
        policy_hash=policy_hash,
        voice_store_sha=store_sha,
        sections=drafted_sections,
        reuse_records=reuse_records,
        input_schema_gaps=list(plan.input_schema_gaps),
    )
    any_populated = any(s.section_populated for s in drafted_sections)
    combined_hash = hashlib.sha256(
        "|".join(prompt_hashes).encode("utf-8")
    ).hexdigest() if prompt_hashes else policy_hash
    voice_gate = merge_voice_reports(voice_reports, store_sha)

    response = HistoryDraftResponse(
        package=package,
        section_populated=any_populated,
        empty_reason=None if any_populated else "No History sections had supporting blocks",
        rendered_prose="\n\n".join(rendered_parts),
        review=ReviewQueue(items=all_review),
        tokens_used=tokens_used,
        tokens_by_stage=tokens_by_stage,
        model=model,
        latency_ms=0,
        cost_usd=round(cost_usd, 6),
        prompt_hash=combined_hash,
        structure_spec_hash=spec_hash,
        voice_store_sha=store_sha,
        voice_gate=voice_gate.model_dump(),
    )
    update_history_trace_metadata(
        prompt_hash=combined_hash,
        voice_store_sha=store_sha,
        section_keys=[s.section_key for s in drafted_sections if s.section_populated],
        tokens_used=tokens_used,
        cost_usd=round(cost_usd, 6),
    )
    return attach_langfuse_ids(response)
