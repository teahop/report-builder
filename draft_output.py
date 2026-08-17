"""Draft output helpers — no prompt load.

These used to live in draft.py beside DRAFT_SYSTEM_PROMPT. Relocated so the
History production path can finalize, annotate, and map to ReportSection
without loading the retired draft_prompt.md.
"""

from __future__ import annotations

from draft_validators import filter_blocks_by_trigger, render_prose_from_blocks
from schemas import (
    Conflict,
    Disagreement,
    DraftProseOutput,
    Ledger,
    ReportSection,
    SectionName,
    SourcedFact,
)


def disagreement_to_report_conflict(d: Disagreement, ledger: Ledger) -> Conflict:
    by_id = {f.id: f for f in ledger.facts}
    versions: list[SourcedFact] = []
    for v in d.versions:
        fact = by_id.get(v.fact_id)
        versions.append(
            SourcedFact(
                statement=v.value_text or v.value,
                fact_id=v.fact_id,
                source_id=v.source_id,
                source_date=v.source_date,
                life_stage=fact.life_stage if fact else "current",
                reporter=v.reporter,
            )
        )
    return Conflict(topic=d.topic, versions=versions)


def finalize_draft_output(output: DraftProseOutput, ledger: Ledger) -> DraftProseOutput:
    """
    Blocks are primary; prose and top-level statements are derived from them.

    When `blocks` is empty, preserve the legacy prose-authored path (tests and
    older callers). When blocks are present: drop untriggered blocks (§7),
    render prose deterministically, and flatten per-block statements.
    """

    if not output.blocks:
        return output

    blocks = filter_blocks_by_trigger(output.blocks, ledger)
    prose = render_prose_from_blocks(blocks)
    flattened = [stmt for block in blocks for stmt in block.statements]
    statements = flattened if flattened else list(output.statements)
    return output.model_copy(
        update={
            "blocks": blocks,
            "prose": prose,
            "statements": statements,
        }
    )


def render_annotated_review(output: DraftProseOutput) -> tuple[str, list[str]]:
    """
    Build the annotated review copy from a DraftProseOutput.

    Clean `prose` is for Molly (paste-ready). The annotated copy appends each
    statement's fact_ids at the end of its `quote` span for TJ's verification
    pass. Overlapping / nested spans are expected once sentences fuse — annotate
    at span end; do not attempt fancy interleaving.

    A quote missing from prose is a soft failure: listed in the returned
    unanchored list and reported in the annotated footer ("unanchored: …").
    Never raises.
    """

    prose = output.prose or ""
    unanchored: list[str] = []
    inserts: list[tuple[int, str]] = []

    for stmt in output.statements:
        quote = (stmt.quote or "").strip()
        if not quote:
            unanchored.append(stmt.statement[:120] or "(empty quote)")
            continue
        idx = prose.find(quote)
        if idx < 0:
            unanchored.append(quote)
            continue
        end = idx + len(quote)
        ids = ", ".join(stmt.fact_ids)
        inserts.append((end, f" [{ids}]"))

    inserts.sort(key=lambda pair: pair[0], reverse=True)
    annotated = prose
    for end, marker in inserts:
        annotated = annotated[:end] + marker + annotated[end:]

    if unanchored:
        footer = "\n".join(f"unanchored: {q}" for q in unanchored)
        annotated = f"{annotated}\n\n{footer}" if annotated else footer

    return annotated, unanchored


def output_to_report_section(
    output: DraftProseOutput,
    *,
    section: SectionName,
    ledger: Ledger,
    conflicts: list[Disagreement],
) -> ReportSection:
    by_id = {f.id: f for f in ledger.facts}
    facts: list[SourcedFact] = []
    for stmt in output.statements:
        for fact_id in stmt.fact_ids:
            fact = by_id[fact_id]
            facts.append(
                SourcedFact(
                    statement=stmt.statement,
                    fact_id=fact.id,
                    source_id=fact.source_id,
                    source_date=fact.source_date,
                    life_stage=fact.life_stage,
                    reporter=fact.reporter,
                )
            )
    return ReportSection(
        section=section,
        prose=output.prose,
        facts=facts,
        conflicts=[disagreement_to_report_conflict(c, ledger) for c in conflicts],
        coverage=output.coverage or sorted({f.life_stage for f in facts}),
    )


# Private alias so existing internal call sites can switch with a one-line import.
_output_to_report_section = output_to_report_section
_disagreement_to_report_conflict = disagreement_to_report_conflict
