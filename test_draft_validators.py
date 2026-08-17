"""Focused draft-validator tests. No live model."""

from __future__ import annotations

import json
import re
from pathlib import Path

from draft_validators import (
    review_items_from_visible_fact_ids,
    validate_prose_has_no_fact_ids,
)
from schemas import (
    Child,
    DraftBlock,
    DraftBlockKind,
    DraftProseOutput,
    Fact,
    Ledger,
    Source,
)

_DIR = Path(__file__).resolve().parent
_SMOKE_215618 = _DIR / "evals/history/traces/smoke-20260814-215618.jsonl"
_LABEL = re.compile(r"\*\*(.+?):\*\*\s*")


def _fact(fid: str) -> Fact:
    return Fact(
        id=fid,
        subject="child",
        predicate="family_history",
        value="x",
        value_text="x",
        qualifier=None,
        assertion="asserted",
        source_id="src_1",
        source_date="2013-09-10",
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


def _ledger_for_ids(ids: list[str]) -> Ledger:
    return Ledger(
        child=Child(
            name="Emma Rose Callahan", dob="2010-01-01", evaluation_date="2025-06-01"
        ),
        ledger_version="test",
        built_at="2026-08-14T00:00:00Z",
        sources=[
            Source(
                id="src_1",
                type="prior_eval",
                date="2013-09-10",
                label="Prior eval",
                content="notes",
                doc_class="narrative",
            )
        ],
        facts=[_fact(fid) for fid in ids],
    )


def _blocks_from_section_prose(prose: str) -> list[DraftBlock]:
    matches = list(_LABEL.finditer(prose))
    blocks: list[DraftBlock] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prose)
        body = prose[start:end].strip()
        blocks.append(
            DraftBlock(
                kind=DraftBlockKind.PROSE,
                label=match.group(1),
                prose=body or " ",
            )
        )
    return blocks


def _output_from_smoke_sections(record: dict, section_keys: list[str]) -> DraftProseOutput:
    blocks: list[DraftBlock] = []
    proses: list[str] = []
    for section in record["sections"]:
        if section["section_key"] not in section_keys:
            continue
        proses.append(section["prose"])
        blocks.extend(_blocks_from_section_prose(section["prose"]))
    return DraftProseOutput(blocks=blocks, prose="\n\n".join(proses), statements=[])


def test_decisions_20260728_ids_stay_out_of_prose() -> None:
    """DECISIONS.md 2026-07-28: visible f_… ids stay out of prose.

    Fixture is the stored fixture_001 draft from smoke-20260814-215618:
    three trailing (fact_ids: …) in Current Status & History, plus five inline
    (f_doc_26_005)-style ids in Previous Evaluations.
    """

    record = json.loads(_SMOKE_215618.read_text(encoding="utf-8"))
    output = _output_from_smoke_sections(
        record, ["current_status_history", "previous_evaluations"]
    )
    assert "fact_ids:" in output.prose
    assert "(f_doc_26_005)" in output.prose
    assert any(b.label == "Family History" for b in output.blocks)
    assert any(b.label == "Previous Evaluations" for b in output.blocks)

    # Membership against the ids that actually appear in this stored string.
    leaked = [
        "f_doc_26_008",
        "f_doc_11_014",
        "f_doc_25_018",
        "f_doc_25_008",
        "f_doc_26_006",
        "f_doc_26_005",
        "f_doc_11_009",
        "f_doc_11_010",
        "f_doc_25_010",
        "f_doc_25_017",
        "f_doc_25_011",
        "f_doc_26_009",
        "f_doc_26_010",
        "f_doc_26_013",
        "f_doc_26_014",
    ]
    ledger = _ledger_for_ids(leaked + ["f_decoy_not_in_prose"])
    errors = validate_prose_has_no_fact_ids(output, ledger)
    assert errors, "stored 215618 prose leaks ledger ids; validator must reject"
    blob = " ".join(errors)
    assert "f_doc_26_008" in blob
    assert "f_doc_26_005" in blob
    assert "fact_id" in blob.lower()
    assert "f_decoy_not_in_prose" not in blob

    # Clean prose with a lookalike that is not on this ledger must not fire.
    clean = DraftProseOutput(
        blocks=[
            DraftBlock(
                kind=DraftBlockKind.PROSE,
                label="Family History",
                prose="Emma has a family history of suspected neglect.",
            )
        ],
        prose=(
            "**Family History:** Emma has a family history of suspected neglect. "
            "See f_not_on_this_ledger_001 for an unrelated token."
        ),
        statements=[],
    )
    assert validate_prose_has_no_fact_ids(clean, ledger) == []

    # Trailer marker still fires when the model invents an id absent from the ledger.
    invented = DraftProseOutput(
        blocks=[
            DraftBlock(
                kind=DraftBlockKind.PROSE,
                label="Family History",
                prose="Neglect was suspected (fact_ids: f_invented_999).",
            )
        ],
        prose="**Family History:** Neglect was suspected (fact_ids: f_invented_999).",
        statements=[],
    )
    invented_errors = validate_prose_has_no_fact_ids(invented, ledger)
    assert invented_errors
    assert any("fact_ids:" in e for e in invented_errors)

    queued = review_items_from_visible_fact_ids(output, ledger)
    assert queued
    assert all(item.kind == "visible_fact_id" for item in queued)
    assert all(item.requires_decision is False for item in queued)


if __name__ == "__main__":
    tests = [test_decisions_20260728_ids_stay_out_of_prose]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
