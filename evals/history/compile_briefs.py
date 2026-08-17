"""Compile provisional_tj_v1 evidence briefs from the fixture_001 cache — no LLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from conflicts import detect_disagreements_from_ledger  # noqa: E402
from history_compiler import (  # noqa: E402
    case_brief_json,
    compile_history_plan,
    render_evidence_brief_markdown,
)
from schemas import Ledger  # noqa: E402

_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_OUT = _WEEK1 / "evals" / "history" / "briefs"


def main() -> None:
    raw = json.loads(_CACHE.read_text(encoding="utf-8"))
    ledger = Ledger.model_validate(raw["ledger"])
    conflicts, variance, *_ = detect_disagreements_from_ledger(ledger)
    plan = compile_history_plan(ledger, structure_spec_id="provisional_tj_v1")
    _OUT.mkdir(parents=True, exist_ok=True)

    summary_lines = [
        "# Compiled History evidence briefs (no model)",
        "",
        f"structure_spec_id: `{plan.structure_spec_id}`",
        f"facts_in_ledger: {len(ledger.facts)}",
        f"evaluation_date: `{ledger.child.evaluation_date}`",
        f"exclusions: {len(plan.exclusions)}",
        f"review_queue: {len(plan.review_queue)}",
        "",
        "## Sections / blocks",
    ]
    for section in plan.sections:
        summary_lines.append(
            f"- `{section.section_key}` ({section.display_label}) blocks={len(section.blocks)}"
        )
        for b in section.blocks:
            summary_lines.append(
                f"  - `{b.block_key}` fact_ids={len(b.fact_ids)}"
            )
    summary_lines.append("")
    summary_lines.append("## Input-schema gaps")
    for g in plan.input_schema_gaps:
        summary_lines.append(f"- {g}")
    summary_lines.append("")

    paths: list[Path] = []
    for section in plan.sections:
        md = render_evidence_brief_markdown(
            plan, section, ledger, conflicts=conflicts, variance=variance
        )
        md_path = _OUT / f"{section.section_key}.md"
        md_path.write_text(md, encoding="utf-8")
        paths.append(md_path)

        brief = case_brief_json(
            plan,
            section,
            ledger,
            conflicts=conflicts,
            variance=variance,
            reuse_records=[],
            fewshots=[],
        )
        json_path = _OUT / f"{section.section_key}.json"
        json_path.write_text(brief + "\n", encoding="utf-8")
        paths.append(json_path)

    audit = {
        "exclusions": [
            {
                "fact_id": e.fact_id,
                "predicate": e.predicate,
                "destination": e.destination,
                "reason": e.reason,
                "source_label": e.source_label,
                "as_of_date": e.as_of_date,
                "value_text": e.value_text,
            }
            for e in plan.exclusions
        ],
        "review_queue": [
            {
                "fact_id": e.fact_id,
                "predicate": e.predicate,
                "destination": e.destination,
                "reason": e.reason,
                "source_label": e.source_label,
                "as_of_date": e.as_of_date,
                "value_text": e.value_text,
            }
            for e in plan.review_queue
        ],
    }
    audit_path = _OUT / "routing_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    paths.append(audit_path)

    index = _OUT / "README.md"
    summary_lines.append("## Artifacts")
    for p in paths:
        summary_lines.append(f"- `{p.relative_to(_WEEK1)}`")
    index.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Wrote {index}")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
