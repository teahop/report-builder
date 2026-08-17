"""Rebuild fixture_001 ledger cache via extraction path + extract gates.

Writes ``evals/cache/fixture_001_ledger.json``. Prefer a live extract; always
apply deterministic extract skip gates so known wrong predicate bags cannot
remain in the cache. Does not hand-edit fact values.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from extract import ExtractedFactDraft, _draft_is_skippable  # noqa: E402
from schemas import Fact, Ledger, Source  # noqa: E402

_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_AB_CACHE = _WEEK1 / "fixtures" / "fixture_001" / "_ab_ledger_cache.json"


def _fact_as_draft(fact: Fact) -> ExtractedFactDraft:
    return ExtractedFactDraft.model_validate(
        {
            "subject": fact.subject,
            "predicate": fact.predicate,
            "value": fact.value,
            "value_text": fact.value_text,
            "qualifier": fact.qualifier,
            "assertion": fact.assertion,
            "life_stage": fact.life_stage,
            "grade": fact.grade,
            "confidence": fact.confidence,
            "temporality": fact.temporality,
            "reporter": fact.reporter,
            "as_of_date": fact.as_of_date,
            "source_section": fact.source_section,
            "valence": fact.valence,
        }
    )


def apply_extract_gates(ledger: Ledger) -> tuple[Ledger, list[dict]]:
    """Drop facts that current extract skip filters would reject."""

    sources = {s.id: s for s in ledger.sources}
    kept: list[Fact] = []
    dropped: list[dict] = []
    for fact in ledger.facts:
        src = sources.get(fact.source_id)
        draft = _fact_as_draft(fact)
        if _draft_is_skippable(draft, src):
            dropped.append(
                {
                    "fact_id": fact.id,
                    "predicate": fact.predicate,
                    "value": fact.value,
                    "value_text": fact.value_text,
                    "source_id": fact.source_id,
                    "reason": "extract_gate_skippable",
                }
            )
            continue
        kept.append(fact)
    return ledger.model_copy(update={"facts": kept}), dropped


def _try_live_extract() -> Ledger | None:
    load_dotenv(_WEEK1 / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not available — skipping live extract")
        return None
    from draft_fixture001_scale import _build_fixture_001_ledger
    from provider import ModelProvider

    print("Live-extracting fixture_001…")
    provider = ModelProvider()
    ledger, model, tokens_by_source, pt, ct, failures = _build_fixture_001_ledger(
        provider
    )
    print(
        f"  extract complete model={model} facts={len(ledger.facts)} "
        f"prompt_tok={pt} completion_tok={ct} failures={len(failures)}"
    )
    for src_id, n in tokens_by_source.items():
        print(f"  tokens[{src_id}]={n}")
    return ledger


def _load_existing() -> Ledger:
    for path in (_CACHE, _AB_CACHE):
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            print(f"Loading existing ledger from {path}")
            return Ledger.model_validate(raw["ledger"])
    raise SystemExit("No existing ledger cache to gate-replay")


def main() -> None:
    model = "gate-replay"
    ledger = _try_live_extract()
    if ledger is None:
        ledger = _load_existing()
    else:
        model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    gated, dropped = apply_extract_gates(ledger)
    print(f"Extract gates dropped {len(dropped)} facts; kept {len(gated.facts)}")
    for row in dropped:
        print(
            f"  DROP {row['fact_id']} {row['predicate']}: "
            f"{(row['value_text'] or row['value'])[:90]!r}"
        )

    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "extract_gates_dropped": dropped,
        "ledger": gated.model_dump(mode="json"),
    }
    _CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {_CACHE} ({len(gated.facts)} facts)")


if __name__ == "__main__":
    main()
