"""Deterministic History case-brief compiler (Layer 3) — no LLM planner."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from conflicts import compute_timelines
from history_evidence import (
    ExclusionRecord,
    attribution_for_fact,
    group_source_local_episodes,
    is_future_of_evaluation,
    variance_is_meaningful,
)
from history_fewshots import FewShotExample, select_fewshots
from history_schemas import FactReuseRecord
from history_selectors import (
    rater_block_key,
    rater_display_label,
    run_selector,
    select_rater_input,
)
from history_structure import load_structure_spec
from schemas import Disagreement, Fact, Ledger, Timeline


@dataclass
class PlannedBlock:
    block_key: str
    display_label: str
    kind: str
    purpose: str
    selector: str
    fact_ids: list[str]
    facts: list[Fact]
    legacy_trigger: str | None = None
    input_schema_gap: str | None = None


@dataclass
class PlannedSection:
    section_key: str
    display_label: str
    purpose: str
    outline_trigger: str
    blocks: list[PlannedBlock] = field(default_factory=list)


@dataclass
class CompiledHistoryPlan:
    structure_spec_id: str
    sections: list[PlannedSection]
    input_schema_gaps: list[str] = field(default_factory=list)
    exclusions: list[ExclusionRecord] = field(default_factory=list)
    review_queue: list[ExclusionRecord] = field(default_factory=list)


def claim_and_source_wording(
    value: object | None,
    value_text: object | None,
) -> tuple[str, str | None]:
    """Normalized claim to narrate, plus the source span when it adds wording.

    Empty ``value`` falls back to the span alone so a brief never emits a blank
    claim. Matching claim and span (case-fold, collapsed whitespace) are not
    repeated. This does not repair a corrupted span; it only leads with the
    claim sitting beside it.
    """

    claim = str(value or "").strip()
    span = str(value_text or "").strip()
    if not claim:
        return span, None
    if not span or _wording_matches(claim, span):
        return claim, None
    return claim, span


def _wording_matches(left: str, right: str) -> bool:
    return " ".join(left.split()).casefold() == " ".join(right.split()).casefold()


def format_fact_evidence_lines(
    predicate: str,
    value: object | None,
    value_text: object | None,
) -> list[str]:
    """Claim-first fact bullet; source wording is a labeled sub-bullet.

    Ledger ids stay out of this rendering. ``build_case_brief`` keeps them on
    the structured payload for code.
    """

    claim, source = claim_and_source_wording(value, value_text)
    lines = [f"- **{predicate}** · {claim}"]
    if source:
        lines.append(f'  - source wording: "{source}"')
    return lines


def _fact_dict(f: Fact, ledger: Ledger) -> dict:
    attr = attribution_for_fact(f, ledger)
    claim, source = claim_and_source_wording(f.value, f.value_text)
    payload = {
        "fact_id": f.id,
        "subject": f.subject,
        "predicate": f.predicate,
        "qualifier": f.qualifier,
        "claim": claim,
        "value": f.value,
        "value_text": f.value_text,
        "assertion": f.assertion,
        "source_id": f.source_id,
        "source_date": f.source_date,
        "as_of_date": f.as_of_date,
        "reporter": f.reporter,
        "attribution": attr["attribution"],
        "source_label": attr["source_label"],
        "life_stage": f.life_stage,
        "grade": f.grade,
        "temporality": f.temporality,
        "confidence": f.confidence,
        "derivation": f.derivation,
        "source_section": f.source_section,
    }
    if source:
        payload["source_wording"] = source
    return payload


def _exclusion_dict(rec: ExclusionRecord) -> dict:
    return {
        "fact_id": rec.fact_id,
        "predicate": rec.predicate,
        "destination": rec.destination,
        "reason": rec.reason,
        "source_id": rec.source_id,
        "source_label": rec.source_label,
        "source_date": rec.source_date,
        "as_of_date": rec.as_of_date,
        "value_text": rec.value_text,
    }


def _timeline_payload(timelines: list[Timeline], fact_ids: set[str]) -> list[dict]:
    """Timelines reference fact ids only — do not re-copy full claim text."""

    out: list[dict] = []
    for t in timelines:
        entries = [e for e in t.entries if e.fact_id in fact_ids]
        if not entries:
            continue
        out.append(
            {
                "subject": t.subject,
                "predicate": t.predicate,
                "qualifier": t.qualifier,
                "topic": t.topic,
                "fact_ids": [e.fact_id for e in entries],
                "latest_fact_id": next(
                    (e.fact_id for e in entries if e.is_latest), entries[-1].fact_id
                ),
            }
        )
    return out


def _filter_disagreements(
    items: list[Disagreement],
    fact_ids: set[str],
    *,
    require_meaningful_variance: bool = False,
) -> list[dict]:
    out: list[dict] = []
    for d in items:
        versions = [v for v in d.versions if v.fact_id in fact_ids]
        if not versions:
            continue
        version_dicts = [
            {
                "fact_id": v.fact_id,
                "source_id": v.source_id,
                "source_date": v.source_date,
                "reporter": v.reporter,
                "value": v.value,
                "assertion": v.assertion,
            }
            for v in versions
        ]
        if require_meaningful_variance and not variance_is_meaningful(version_dicts):
            continue
        out.append(
            {
                "topic": d.topic,
                "subject": d.subject,
                "predicate": d.predicate,
                "qualifier": d.qualifier,
                "predicate_class": d.predicate_class,
                "fact_ids": [v["fact_id"] for v in version_dicts],
                "versions": version_dicts,
            }
        )
    return out


def _merge_audit(
    plan_exclusions: list[ExclusionRecord],
    plan_review: list[ExclusionRecord],
    result_exclusions: list,
    result_review: list,
) -> None:
    plan_exclusions.extend(result_exclusions)
    plan_review.extend(result_review)


def compile_history_plan(
    ledger: Ledger,
    *,
    structure_spec_id: str = "provisional_tj_v1",
) -> CompiledHistoryPlan:
    spec = load_structure_spec(structure_spec_id)
    gaps: list[str] = []
    planned_sections: list[PlannedSection] = []
    all_exclusions: list[ExclusionRecord] = []
    all_review: list[ExclusionRecord] = []

    for section in spec["sections"]:
        planned_blocks: list[PlannedBlock] = []
        for block in section["blocks"]:
            gap = block.get("input_schema_gap")
            if isinstance(gap, str) and gap.strip():
                gaps.append(f"{block['block_key']}: {gap.strip()}")

            if block.get("dynamic") and block.get("selector") == "rater_input":
                for rater, facts, sel in select_rater_input(ledger):
                    _merge_audit(
                        all_exclusions, all_review, sel.exclusions, sel.review_queue
                    )
                    planned_blocks.append(
                        PlannedBlock(
                            block_key=rater_block_key(rater),
                            display_label=rater_display_label(rater),
                            kind=block.get("kind", "prose"),
                            purpose=block.get("purpose") or section["purpose"],
                            selector="rater_input",
                            fact_ids=[f.id for f in facts],
                            facts=list(facts),
                            legacy_trigger=None,
                            input_schema_gap=None,
                        )
                    )
                continue

            result = run_selector(block["selector"], ledger)
            _merge_audit(
                all_exclusions, all_review, result.exclusions, result.review_queue
            )
            if not result.facts:
                continue
            planned_blocks.append(
                PlannedBlock(
                    block_key=block["block_key"],
                    display_label=block["display_label"],
                    kind=block.get("kind", "prose"),
                    purpose=block.get("purpose") or section["purpose"],
                    selector=block["selector"],
                    fact_ids=[f.id for f in result.facts],
                    facts=list(result.facts),
                    legacy_trigger=block.get("legacy_trigger"),
                    input_schema_gap=gap if isinstance(gap, str) else None,
                )
            )

        outline = section.get("outline_trigger", "evidence")
        # Always-offered sections still omit empty filler: include only when
        # blocks resolved, except we record the section in the outline sense
        # via gaps. Model calls only happen for sections with blocks.
        if planned_blocks or outline == "always":
            planned_sections.append(
                PlannedSection(
                    section_key=section["section_key"],
                    display_label=section["display_label"],
                    purpose=section["purpose"],
                    outline_trigger=outline,
                    blocks=planned_blocks,
                )
            )

    # Deduplicate gap strings while preserving order.
    seen: set[str] = set()
    unique_gaps: list[str] = []
    for g in gaps:
        if g not in seen:
            seen.add(g)
            unique_gaps.append(g)

    # Global future-dated audit — surface even when no thematic selector claimed them.
    already_review = {e.fact_id for e in all_review}
    sources = {s.id: s for s in ledger.sources}
    for fact in ledger.facts:
        if fact.id in already_review:
            continue
        if not is_future_of_evaluation(fact, ledger.child.evaluation_date):
            continue
        src = sources.get(fact.source_id)
        all_review.append(
            ExclusionRecord(
                fact_id=fact.id,
                predicate=fact.predicate,
                destination="ledger_global",
                reason="as_of_or_source_date_after_evaluation_date",
                source_id=fact.source_id,
                source_label=src.label if src is not None else fact.source_id,
                source_date=src.date if src is not None else fact.source_date,
                as_of_date=fact.as_of_date,
                value_text=(fact.value_text or fact.value or "")[:240],
            )
        )

    return CompiledHistoryPlan(
        structure_spec_id=structure_spec_id,
        sections=planned_sections,
        input_schema_gaps=unique_gaps,
        exclusions=all_exclusions,
        review_queue=all_review,
    )


def build_case_brief(
    plan: CompiledHistoryPlan,
    section: PlannedSection,
    ledger: Ledger,
    *,
    conflicts: list[Disagreement],
    variance: list[Disagreement],
    reuse_records: list[FactReuseRecord],
    fewshots: list[FewShotExample],
) -> dict[str, Any]:
    """One deterministic brief per populated top-level History section."""

    source_labels = {
        s.id: {"label": s.label, "date": s.date, "type": s.type} for s in ledger.sources
    }
    section_fact_ids = {fid for b in section.blocks for fid in b.fact_ids}
    timelines = compute_timelines(ledger.facts)

    block_recipes = [
        {
            "block_key": b.block_key,
            "display_label": b.display_label,
            "kind": b.kind,
            "purpose": b.purpose,
            "fact_ids": b.fact_ids,
            "legacy_trigger": b.legacy_trigger,
        }
        for b in section.blocks
    ]

    facts_by_block = {
        b.block_key: [_fact_dict(f, ledger) for f in b.facts] for b in section.blocks
    }

    episodes_by_block: dict[str, list[dict]] = {}
    for b in section.blocks:
        episodes = group_source_local_episodes(b.facts, ledger)
        episodes_by_block[b.block_key] = [
            {
                "episode_id": ep.episode_id,
                "source_id": ep.source_id,
                "source_label": ep.source_label,
                "source_date": ep.source_date,
                "as_of_date": ep.as_of_date,
                "source_section": ep.source_section,
                "fact_ids": list(ep.fact_ids),
            }
            for ep in episodes
        ]

    # Compact guidance: facts eligible again here that already appeared earlier.
    # Prior use does not suppress eligibility — it only warns against prose recycling.
    reuse_context = [
        {
            "fact_id": r.fact_id,
            "earlier_section_key": r.section_key,
            "earlier_block_key": r.block_key,
            "earlier_purpose": r.purpose,
        }
        for r in reuse_records
        if r.fact_id in section_fact_ids
    ]

    fewshot_payload = [
        {
            "demonstrates": ex.demonstrates,
            "evidence_shape": ex.evidence_shape,
            "input_brief": ex.input_brief,
            "output": ex.output,
        }
        for ex in fewshots
    ]

    def _belongs_to_section(destination: str) -> bool:
        if destination in {b.block_key for b in section.blocks}:
            return True
        if destination in {b.selector for b in section.blocks}:
            return True
        if section.section_key == "rater_input" and destination.startswith("rater_input:"):
            return True
        if (
            section.section_key == "previous_evaluations"
            and destination == "previous_evaluations"
        ):
            return True
        if section.section_key == "current_status_history" and destination in {
            "family_history",
            "birth_developmental_history",
            "health_history",
            "social_history",
            "nurse_report",
        }:
            return True
        if section.section_key == "educational_history" and destination.startswith(
            "educational_"
        ):
            return True
        return False

    section_exclusions = [
        _exclusion_dict(e) for e in plan.exclusions if _belongs_to_section(e.destination)
    ]
    section_review = [
        _exclusion_dict(e)
        for e in plan.review_queue
        if _belongs_to_section(e.destination)
    ]

    return {
        "structure_spec_id": plan.structure_spec_id,
        "section_key": section.section_key,
        "display_label": section.display_label,
        "purpose": section.purpose,
        "eligible_blocks": block_recipes,
        "instruction": (
            "Draft only the eligible_blocks, in order, using exact display_label "
            "values as DraftBlock.label. Do not invent blocks or absence filler. "
            "Evidence is grouped into source-local episodes — keep related facts "
            "together. reuse_context lists facts already used earlier — reuse for "
            "this section's purpose is allowed; copied prose is not. "
            "review_queue facts are dated after evaluation_date and must not be "
            "stated as current case evidence."
        ),
        "child": ledger.child.model_dump(),
        "source_labels": source_labels,
        "facts_by_block": facts_by_block,
        "episodes_by_block": episodes_by_block,
        "timelines": _timeline_payload(timelines, section_fact_ids),
        "must_mention_conflicts": _filter_disagreements(conflicts, section_fact_ids),
        "variance": _filter_disagreements(
            variance, section_fact_ids, require_meaningful_variance=True
        ),
        "reuse_context": reuse_context,
        "exclusions": section_exclusions,
        "review_queue": section_review,
        "fewshots": fewshot_payload,
    }


def case_brief_json(
    plan: CompiledHistoryPlan,
    section: PlannedSection,
    ledger: Ledger,
    *,
    conflicts: list[Disagreement],
    variance: list[Disagreement],
    reuse_records: list[FactReuseRecord],
    fewshots: list[FewShotExample] | None = None,
) -> str:
    shots = fewshots
    if shots is None:
        shots = select_fewshots(
            structure_spec_id=plan.structure_spec_id,
            section_key=section.section_key,
            block_keys=[b.block_key for b in section.blocks],
            evidence_shape="ordinary",
            limit=2,
        )
    brief = build_case_brief(
        plan,
        section,
        ledger,
        conflicts=conflicts,
        variance=variance,
        reuse_records=reuse_records,
        fewshots=shots,
    )
    return json.dumps(brief, indent=2, sort_keys=True)


_LEDGER_ID_KEYS = frozenset({"fact_id", "fact_ids", "latest_fact_id"})


def strip_ledger_ids_from_brief(payload: Any) -> Any:
    """Drop ledger-id fields from a brief so the drafting model cannot copy them."""

    if isinstance(payload, dict):
        return {
            key: strip_ledger_ids_from_brief(value)
            for key, value in payload.items()
            if key not in _LEDGER_ID_KEYS
        }
    if isinstance(payload, list):
        return [strip_ledger_ids_from_brief(item) for item in payload]
    return payload


def model_facing_case_brief_json(
    plan: CompiledHistoryPlan,
    section: PlannedSection,
    ledger: Ledger,
    *,
    conflicts: list[Disagreement],
    variance: list[Disagreement],
    reuse_records: list[FactReuseRecord],
    fewshots: list[FewShotExample] | None = None,
) -> str:
    """JSON brief for the drafting call — same payload as code, without ledger ids."""

    shots = fewshots
    if shots is None:
        shots = select_fewshots(
            structure_spec_id=plan.structure_spec_id,
            section_key=section.section_key,
            block_keys=[b.block_key for b in section.blocks],
            evidence_shape="ordinary",
            limit=2,
        )
    brief = build_case_brief(
        plan,
        section,
        ledger,
        conflicts=conflicts,
        variance=variance,
        reuse_records=reuse_records,
        fewshots=shots,
    )
    return json.dumps(
        strip_ledger_ids_from_brief(brief), indent=2, sort_keys=True
    )


def render_evidence_brief_markdown(
    plan: CompiledHistoryPlan,
    section: PlannedSection,
    ledger: Ledger,
    *,
    conflicts: list[Disagreement] | None = None,
    variance: list[Disagreement] | None = None,
) -> str:
    """Human-readable compiled evidence brief — no LLM call."""

    brief = build_case_brief(
        plan,
        section,
        ledger,
        conflicts=conflicts or [],
        variance=variance or [],
        reuse_records=[],
        fewshots=[],
    )
    lines: list[str] = [
        f"# {brief['display_label']}",
        "",
        f"structure_spec_id: `{brief['structure_spec_id']}`",
        f"section_key: `{brief['section_key']}`",
        f"purpose: `{brief['purpose']}`",
        f"evaluation_date: `{ledger.child.evaluation_date}`",
        "",
    ]

    if not section.blocks:
        lines.append("_No supported blocks for this section._")
        lines.append("")
    for block in section.blocks:
        lines.append(f"## {block.display_label} (`{block.block_key}`)")
        lines.append("")
        episodes = brief["episodes_by_block"].get(block.block_key, [])
        facts = {f["fact_id"]: f for f in brief["facts_by_block"].get(block.block_key, [])}
        if not episodes:
            lines.append("_No eligible facts._")
            lines.append("")
            continue
        for ep in episodes:
            header = (
                f"### Episode `{ep['episode_id']}` — {ep['source_label']} "
                f"(source_date={ep['source_date']}, as_of={ep['as_of_date']})"
            )
            lines.append(header)
            if ep.get("source_section"):
                lines.append(f"source_section: {ep['source_section']}")
            lines.append("")
            for fid in ep["fact_ids"]:
                f = facts.get(fid)
                if not f:
                    continue
                lines.extend(
                    format_fact_evidence_lines(
                        str(f["predicate"]),
                        f.get("value"),
                        f.get("value_text"),
                    )
                )
                lines.append(
                    f"  - destination: `{section.section_key}/{block.block_key}`"
                )
                lines.append(
                    f"  - attribution: {f.get('attribution')} "
                    f"(reporter={f.get('reporter')!r}, source_label={f.get('source_label')!r})"
                )
                lines.append(
                    f"  - dates: source={f.get('source_date')}, as_of={f.get('as_of_date')}"
                )
            lines.append("")

    review = brief.get("review_queue") or []
    excl = brief.get("exclusions") or []
    if review:
        lines.append("## Review queue (after evaluation_date — not current evidence)")
        lines.append("")
        for e in review:
            lines.append(
                f"- `{e['fact_id']}` · {e['predicate']} · destination=`{e['destination']}` "
                f"· reason=`{e['reason']}` · as_of={e.get('as_of_date')} "
                f"· source={e.get('source_label')!r}"
            )
            lines.append(f"  - {e.get('value_text')}")
        lines.append("")
    if excl:
        lines.append("## Exclusions")
        lines.append("")
        for e in excl:
            lines.append(
                f"- `{e['fact_id']}` · {e['predicate']} · destination=`{e['destination']}` "
                f"· reason=`{e['reason']}` · source={e.get('source_label')!r}"
            )
            lines.append(f"  - {e.get('value_text')}")
        lines.append("")

    if brief.get("timelines"):
        lines.append("## Timelines (fact_id references only)")
        lines.append("")
        for t in brief["timelines"]:
            lines.append(
                f"- {t['topic']}: fact_ids={t['fact_ids']} latest=`{t['latest_fact_id']}`"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def compile_section_briefs(
    ledger: Ledger,
    *,
    conflicts: list[Disagreement] | None = None,
    variance: list[Disagreement] | None = None,
    structure_spec_id: str = "provisional_tj_v1",
) -> dict[str, Any]:
    """Compile inspectable per-section briefs — no model call."""

    plan = compile_history_plan(ledger, structure_spec_id=structure_spec_id)
    conflicts = conflicts or []
    variance = variance or []
    sections: list[dict[str, Any]] = []
    for section in plan.sections:
        fact_ids: list[str] = []
        for block in section.blocks:
            fact_ids.extend(block.fact_ids)
        sections.append(
            {
                "section_key": section.section_key,
                "display_label": section.display_label,
                "purpose": section.purpose,
                "populated": bool(section.blocks),
                "blocks": [b.block_key for b in section.blocks],
                "fact_count": len(fact_ids),
                "markdown": render_evidence_brief_markdown(
                    plan,
                    section,
                    ledger,
                    conflicts=conflicts,
                    variance=variance,
                ),
            }
        )
    return {
        "structure_spec_id": plan.structure_spec_id,
        "sections": sections,
        "input_schema_gaps": list(plan.input_schema_gaps),
    }
