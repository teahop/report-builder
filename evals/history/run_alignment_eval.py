"""Offline alignment eval against stored History smokes. No path change.

Reports (a) claim coverage, (b) optional entailment precision, (c) disagreement
with the model's own statement_fact_ids. Model ids are not ground truth.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from dotenv import load_dotenv

load_dotenv(_WEEK1 / ".env")

from draft_validators import check_entailment_one  # noqa: E402
from derived import is_derived_fact  # noqa: E402
from history_align import (  # noqa: E402
    align_prose_to_facts,
    facts_for_ids,
    split_labeled_blocks,
    substantive_sentence_count,
)
from provider import ModelProvider  # noqa: E402
from schemas import Ledger  # noqa: E402

_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_TRACES = _WEEK1 / "evals" / "history" / "traces"
_DEFAULT_SMOKES = (
    "smoke-20260814-214937.jsonl",
    "smoke-20260814-215618.jsonl",
)


def _load_ledger() -> Ledger:
    raw = json.loads(_CACHE.read_text(encoding="utf-8"))
    return Ledger.model_validate(raw["ledger"] if "ledger" in raw else raw)


def _load_smoke(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bodies_by_label(section_prose: str) -> dict[str, str]:
    return {label: body for label, body in split_labeled_blocks(section_prose)}


def align_smoke_section(section: dict, ledger: Ledger) -> list[dict]:
    bodies = _bodies_by_label(section.get("prose") or "")
    rows: list[dict] = []
    for block in section.get("blocks") or []:
        if block.get("kind") != "prose":
            continue
        body = bodies.get(block["display_label"], "")
        facts = facts_for_ids(ledger, block.get("fact_ids") or [])
        statements = align_prose_to_facts(
            body, facts, exclude_name=ledger.child.name
        )
        claim_n = substantive_sentence_count(body)
        covered = len(statements)
        rows.append(
            {
                "section_key": section["section_key"],
                "block_key": block["block_key"],
                "label": block["display_label"],
                "candidate_fact_ids": list(block.get("fact_ids") or []),
                "claim_sentences": claim_n,
                "aligned_statements": [
                    {
                        "quote": s.quote,
                        "statement": s.statement,
                        "fact_ids": list(s.fact_ids),
                    }
                    for s in statements
                ],
                "aligned_fact_ids": [fid for s in statements for fid in s.fact_ids],
                "coverage": (covered / claim_n) if claim_n else None,
            }
        )
    return rows


def _model_id_set(section: dict) -> set[str]:
    out: set[str] = set()
    for group in section.get("statement_fact_ids") or []:
        out.update(group)
    return out


def _flatten_aligned_ids(rows: list[dict]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        out.update(row["aligned_fact_ids"])
    return out


def _disagreements(section: dict, rows: list[dict]) -> list[dict]:
    model_ids = _model_id_set(section)
    aligned_ids = _flatten_aligned_ids(rows)
    only_model = sorted(model_ids - aligned_ids)
    only_align = sorted(aligned_ids - model_ids)
    spans = []
    for row in rows:
        for stmt in row["aligned_statements"]:
            spans.append(
                {
                    "block_key": row["block_key"],
                    "quote": stmt["quote"],
                    "fact_ids": stmt["fact_ids"],
                }
            )
    return [
        {
            "section_key": section["section_key"],
            "model_only_ids": only_model,
            "align_only_ids": only_align,
            "aligned_spans": spans,
        }
    ]


def _run_entailment(
    provider: ModelProvider,
    model: str,
    ledger: Ledger,
    rows: list[dict],
) -> dict:
    by_id = {f.id: f for f in ledger.facts}
    by_source = {s.id: s for s in ledger.sources}
    judged = 0
    supported = 0
    failures: list[dict] = []
    tokens = 0
    for row in rows:
        for stmt in row["aligned_statements"]:
            for fact_id in stmt["fact_ids"]:
                fact = by_id.get(fact_id)
                if fact is None or is_derived_fact(fact):
                    continue
                source = by_source.get(fact.source_id)
                if source is None:
                    failures.append(
                        {
                            "fact_id": fact_id,
                            "statement": stmt["statement"],
                            "reason": "no source",
                        }
                    )
                    judged += 1
                    continue
                ok, rationale, t, *_ = check_entailment_one(
                    provider,
                    model=model,
                    source=source,
                    statement=stmt["statement"],
                )
                tokens += t
                judged += 1
                if ok:
                    supported += 1
                else:
                    failures.append(
                        {
                            "fact_id": fact_id,
                            "statement": stmt["statement"],
                            "reason": rationale,
                        }
                    )
    precision = (supported / judged) if judged else None
    return {
        "judged_pairs": judged,
        "supported": supported,
        "precision": precision,
        "tokens": tokens,
        "failures": failures,
    }


def _print_report(smoke_name: str, payload: dict) -> None:
    print(f"\n=== {smoke_name} ===")
    cov = payload["coverage"]
    print(
        f"coverage: {cov['aligned_statements']}/{cov['claim_sentences']} "
        f"substantive sentences ({cov['rate']:.2%})"
        if cov["claim_sentences"]
        else "coverage: no substantive sentences"
    )
    print(
        f"unique aligned ids: {cov['unique_aligned_ids']} / "
        f"model ids: {cov['unique_model_ids']}"
    )
    ent = payload.get("entailment")
    if ent:
        prec = ent["precision"]
        prec_s = f"{prec:.2%}" if prec is not None else "n/a"
        print(
            f"entailment precision: {ent['supported']}/{ent['judged_pairs']} "
            f"({prec_s})"
        )
        for fail in ent["failures"][:12]:
            print(
                f"  FAIL {fail['fact_id']}: {fail['statement'][:140]!r} "
                f"— {fail['reason'][:160]}"
            )
        if len(ent["failures"]) > 12:
            print(f"  … {len(ent['failures']) - 12} more failures")
    print("disagreement vs model statement_fact_ids (not ground truth):")
    for item in payload["disagreements"]:
        print(f"  {item['section_key']}:")
        print(f"    model-only ids: {item['model_only_ids'] or '—'}")
        print(f"    align-only ids: {item['align_only_ids'] or '—'}")
        for span in item["aligned_spans"]:
            print(
                f"    span {span['block_key']}: {span['quote'][:180]!r} "
                f"→ {span['fact_ids']}"
            )


def evaluate_smoke(
    record: dict,
    ledger: Ledger,
    *,
    provider: ModelProvider | None = None,
    entailment_model: str = "gpt-4o-mini",
) -> dict:
    all_rows: list[dict] = []
    disagreements: list[dict] = []
    model_ids: set[str] = set()
    for section in record.get("sections") or []:
        rows = align_smoke_section(section, ledger)
        all_rows.extend(rows)
        disagreements.extend(_disagreements(section, rows))
        model_ids |= _model_id_set(section)

    claim_sentences = sum(r["claim_sentences"] for r in all_rows)
    aligned_statements = sum(len(r["aligned_statements"]) for r in all_rows)
    aligned_ids = {fid for r in all_rows for fid in r["aligned_fact_ids"]}
    payload: dict = {
        "fixture_id": record.get("fixture_id"),
        "coverage": {
            "claim_sentences": claim_sentences,
            "aligned_statements": aligned_statements,
            "rate": (aligned_statements / claim_sentences) if claim_sentences else 0.0,
            "unique_aligned_ids": sorted(aligned_ids),
            "unique_model_ids": sorted(model_ids),
        },
        "blocks": all_rows,
        "disagreements": disagreements,
    }
    if provider is not None:
        payload["entailment"] = _run_entailment(
            provider, entailment_model, ledger, all_rows
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smokes",
        nargs="*",
        default=list(_DEFAULT_SMOKES),
        help="Trace filenames under evals/history/traces/",
    )
    parser.add_argument(
        "--entailment",
        action="store_true",
        help="Run check_entailment_one on each aligned (span, fact_id) pair.",
    )
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args(argv)

    ledger = _load_ledger()
    provider = ModelProvider() if args.entailment else None
    out_dir = _TRACES
    for name in args.smokes:
        path = _TRACES / name if not Path(name).is_file() else Path(name)
        record = _load_smoke(path)
        payload = evaluate_smoke(
            record, ledger, provider=provider, entailment_model=args.model
        )
        _print_report(path.name, payload)
        out_path = out_dir / f"align-{path.stem}.json"
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
