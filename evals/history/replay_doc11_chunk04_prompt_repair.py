"""Eval-only: one-chunk replay of doc_11_chunk04 after extract_prompt repair.

Uses the retained approved-anonymized user payload from the baseline audit
artifact. Makes exactly one extraction call (gpt-4o-mini, temperature 0).
Does not overwrite prior diagnostic artifacts.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.history.audit_extraction_chunks import (  # noqa: E402
    _process_chunk_drafts,
    _sha256_text,
)
from extract import (  # noqa: E402
    _extraction_user_payload,
)
from provider import EXTRACT_TEMPERATURE, ModelProvider, compute_cost_usd  # noqa: E402
from schemas import Source, SourceExtraction  # noqa: E402
from test_all_stages import load_case_manifest  # noqa: E402

_BASELINE = _WEEK1 / "evals" / "history" / "extraction_audit" / "doc_11_chunk04.json"
_MANIFEST = _WEEK1 / "fixtures" / "fixture_001" / "manifest.json"
_OUT_DIR = (
    _WEEK1
    / "evals"
    / "history"
    / "extraction_audit"
    / "prompt_repair_doc11_chunk04"
)
_EXPECTED_CHUNK_SHA = (
    "6fa5cd841ec5ccd0dd3fdab6a44eb1848eb0ed619fcbc17200d51a86e2438c8a"
)
_BASELINE_PROMPT_SHA = (
    "9096284e4c0acabd32ad53f8194035f5cd678bb3156f2315e88e0b4719aba7a1"
)


def _write_comparison(
    *,
    out_dir: Path,
    baseline: dict[str, Any],
    repaired: dict[str, Any],
    call_meta: dict[str, Any],
) -> Path:
    before_raw = baseline.get("raw_drafts_before_gates") or [
        row["raw_draft"] for row in baseline.get("draft_trace") or []
    ]
    after_raw = repaired.get("raw_drafts_before_gates") or []
    before_disp = [
        {
            "predicate": row["raw_draft"].get("predicate"),
            "value": row["raw_draft"].get("value"),
            "value_text": row["raw_draft"].get("value_text"),
            "skipped": row.get("skipped"),
            "skip_reason": row.get("skip_reason"),
            "retained_fact_id": row.get("retained_fact_id"),
            "resolved_predicate": row.get("resolved_predicate"),
        }
        for row in baseline.get("draft_trace") or []
    ]
    after_disp = [
        {
            "predicate": row["raw_draft"].get("predicate"),
            "proposed_predicate": row["raw_draft"].get("proposed_predicate"),
            "value": row["raw_draft"].get("value"),
            "value_text": row["raw_draft"].get("value_text"),
            "skipped": row.get("skipped"),
            "skip_reason": row.get("skip_reason"),
            "retained_fact_id": row.get("retained_fact_id"),
            "resolved_predicate": row.get("resolved_predicate"),
        }
        for row in repaired.get("draft_trace") or []
    ]

    lines: list[str] = [
        "# Prompt repair comparison — `doc_11_chunk04`",
        "",
        "_One-call diagnostic. Not a pass rate. Anchored to chunk + prompt SHAs._",
        "",
        f"- chunk_sha256: `{repaired['chunk_sha256']}`",
        f"- baseline system_prompt_sha256: `{_BASELINE_PROMPT_SHA}`",
        f"- repaired system_prompt_sha256: `{repaired['system_prompt_sha256']}`",
        f"- model: `{call_meta['model']}` · temperature: `{call_meta['extract_temperature']}`",
        f"- tokens: prompt={call_meta['prompt_tokens']} "
        f"completion={call_meta['completion_tokens']} "
        f"total={call_meta['total_tokens']} "
        f"est_usd={call_meta['estimated_cost_usd']}",
        f"- built_at: `{call_meta['built_at']}`",
        "",
        "## Raw drafts (before gates)",
        "",
        "### Baseline",
        "",
        "```json",
        json.dumps(before_raw, indent=2),
        "```",
        "",
        "### After repair",
        "",
        "```json",
        json.dumps(after_raw, indent=2),
        "```",
        "",
        "## Deterministic dispositions",
        "",
        "### Baseline",
        "",
        "```json",
        json.dumps(before_disp, indent=2),
        "```",
        "",
        "### After repair",
        "",
        "```json",
        json.dumps(after_disp, indent=2),
        "```",
        "",
        "## Retained facts after postprocess",
        "",
        "### Baseline",
        "",
        "```json",
        json.dumps(baseline.get("retained_after_postprocess") or [], indent=2),
        "```",
        "",
        "### After repair",
        "",
        "```json",
        json.dumps(repaired.get("retained_after_postprocess") or [], indent=2),
        "```",
        "",
    ]
    path = out_dir / "comparison.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    load_dotenv(_WEEK1 / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required for one-chunk prompt-repair replay")

    baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
    if baseline.get("chunk_sha256") != _EXPECTED_CHUNK_SHA:
        raise SystemExit(
            f"baseline chunk SHA mismatch: {baseline.get('chunk_sha256')}"
        )
    if baseline.get("system_prompt_sha256") != _BASELINE_PROMPT_SHA:
        raise SystemExit(
            "baseline prompt SHA mismatch — refuse to compare against drifted artifact"
        )

    payload = baseline["user_payload"]
    source_blob = payload["source"]
    content = source_blob["content"]
    if _sha256_text(content) != _EXPECTED_CHUNK_SHA:
        raise SystemExit("retained user_payload content SHA mismatch")

    source = Source.model_validate({**source_blob, "content": content})
    child, _, _ = load_case_manifest(_MANIFEST)

    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    if model != "gpt-4o-mini":
        raise SystemExit(
            f"refusing model={model!r}; this diagnostic requires gpt-4o-mini"
        )

    # Ensure import-time EXTRACT_SYSTEM_PROMPT matches current file.
    import extract as extract_mod

    extract_mod._PROMPT_TEMPLATE = (
        _WEEK1 / "extract_prompt.md"
    ).read_text(encoding="utf-8")
    system_prompt = extract_mod.build_extract_system_prompt()
    extract_mod.EXTRACT_SYSTEM_PROMPT = system_prompt

    provider = ModelProvider()
    # Pass system explicitly so a stale import binding cannot leak the baseline prompt.
    result = provider.complete_structured(
        model=model,
        system=system_prompt,
        user=_extraction_user_payload(source),
        schema=SourceExtraction,
        temperature=EXTRACT_TEMPERATURE,
    )
    assert isinstance(result.data, SourceExtraction)
    drafts = list(result.data.facts)
    total = result.total_tokens
    p_tok = result.prompt_tokens
    c_tok = result.completion_tokens

    processed = _process_chunk_drafts(
        source=source,
        chunk_index=int(baseline["chunk_index"]),
        chunk_count=int(baseline["chunk_count"]),
        chunk_text=content,
        drafts=drafts,
        child=child,
    )
    # Re-stamp with the reloaded prompt SHA (process helper imports module constant).
    processed["system_prompt_sha256"] = _sha256_text(system_prompt)
    processed["user_payload"] = json.loads(_extraction_user_payload(source))
    processed["raw_drafts_before_gates"] = [d.model_dump(mode="json") for d in drafts]
    processed["model"] = model
    processed["prompt_tokens"] = p_tok
    processed["completion_tokens"] = c_tok
    processed["total_tokens"] = total
    processed["origin"] = "prompt_repair_one_chunk_replay"
    processed["baseline_artifact"] = "evals/history/extraction_audit/doc_11_chunk04.json"
    processed["baseline_system_prompt_sha256"] = _BASELINE_PROMPT_SHA
    processed["extract_temperature"] = EXTRACT_TEMPERATURE
    processed["estimated_cost_usd"] = compute_cost_usd(model, p_tok, c_tok)

    if processed["chunk_sha256"] != _EXPECTED_CHUNK_SHA:
        raise SystemExit("replay chunk SHA drifted from baseline")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _OUT_DIR / f"replay-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)

    artifact_path = out_dir / "doc_11_chunk04.json"
    artifact_path.write_text(
        json.dumps(processed, indent=2) + "\n", encoding="utf-8"
    )

    call_meta = {
        "built_at": stamp,
        "model": model,
        "extract_temperature": EXTRACT_TEMPERATURE,
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "total_tokens": total,
        "estimated_cost_usd": processed["estimated_cost_usd"],
        "system_prompt_sha256": processed["system_prompt_sha256"],
        "baseline_system_prompt_sha256": _BASELINE_PROMPT_SHA,
        "chunk_sha256": processed["chunk_sha256"],
        "artifact": str(artifact_path.relative_to(_WEEK1)),
    }
    (out_dir / "run_meta.json").write_text(
        json.dumps(call_meta, indent=2) + "\n", encoding="utf-8"
    )
    comparison = _write_comparison(
        out_dir=out_dir,
        baseline=baseline,
        repaired=processed,
        call_meta=call_meta,
    )

    # Immutable pointer for this repair wave (content-addressed via run stamp dir).
    latest = {
        "replay_dir": str(out_dir.relative_to(_WEEK1)),
        "artifact": str(artifact_path.relative_to(_WEEK1)),
        "comparison": str(comparison.relative_to(_WEEK1)),
        "chunk_sha256": processed["chunk_sha256"],
        "system_prompt_sha256": processed["system_prompt_sha256"],
        "baseline_system_prompt_sha256": _BASELINE_PROMPT_SHA,
        "artifact_sha256": hashlib.sha256(
            artifact_path.read_bytes()
        ).hexdigest(),
    }
    (_OUT_DIR / "LATEST.json").write_text(
        json.dumps(latest, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(latest, indent=2))
    print(
        f"drafts={len(drafts)} tokens={total} "
        f"prompt_sha={processed['system_prompt_sha256'][:12]}…"
    )


if __name__ == "__main__":
    main()
