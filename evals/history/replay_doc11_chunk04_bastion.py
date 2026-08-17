"""Eval-only: one-chunk BastionGPT replay of reviewed doc_11_chunk04.

Holds source chunk, repaired extract prompt, SourceExtraction schema, and
temperature 0 fixed. Provider is the controlled variable. Makes exactly one
Bastion ChatCompletion call. Does not overwrite prior diagnostic artifacts
or change the OpenAI production default.
"""

from __future__ import annotations

import hashlib
import json
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
from extract import _extraction_user_payload  # noqa: E402
from provider import (  # noqa: E402
    BASTION_DEFAULT_MAX_TOKENS,
    BASTION_MODEL,
    EXTRACT_TEMPERATURE,
    BastionAccessError,
    BastionParseError,
    ModelProvider,
    json_mode_system,
)
from schemas import Source, SourceExtraction  # noqa: E402
from test_all_stages import load_case_manifest  # noqa: E402

_BASELINE = _WEEK1 / "evals" / "history" / "extraction_audit" / "doc_11_chunk04.json"
_REPAIRED = (
    _WEEK1
    / "evals"
    / "history"
    / "extraction_audit"
    / "prompt_repair_doc11_chunk04"
    / "replay-20260811T001916Z"
    / "doc_11_chunk04.json"
)
_MANIFEST = _WEEK1 / "fixtures" / "fixture_001" / "manifest.json"
_OUT_DIR = (
    _WEEK1
    / "evals"
    / "history"
    / "extraction_audit"
    / "bastion_doc11_chunk04"
)
_EXPECTED_CHUNK_SHA = (
    "6fa5cd841ec5ccd0dd3fdab6a44eb1848eb0ed619fcbc17200d51a86e2438c8a"
)
_BASELINE_PROMPT_SHA = (
    "9096284e4c0acabd32ad53f8194035f5cd678bb3156f2315e88e0b4719aba7a1"
)
_REPAIRED_PROMPT_SHA = (
    "16d636d260f47dbe307e8317ad7cec17f98efd7b3b5de95c0e266e2f408692af"
)


def _disp_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "predicate": row["raw_draft"].get("predicate"),
            "proposed_predicate": row["raw_draft"].get("proposed_predicate"),
            "value": row["raw_draft"].get("value"),
            "value_text": row["raw_draft"].get("value_text"),
            "grade": row["raw_draft"].get("grade"),
            "skipped": row.get("skipped"),
            "skip_reason": row.get("skip_reason"),
            "retained_fact_id": row.get("retained_fact_id"),
            "resolved_predicate": row.get("resolved_predicate"),
        }
        for row in artifact.get("draft_trace") or []
    ]


def _write_comparison(
    *,
    out_dir: Path,
    baseline: dict[str, Any],
    repaired: dict[str, Any],
    bastion: dict[str, Any],
    call_meta: dict[str, Any],
) -> Path:
    lines: list[str] = [
        "# BastionGPT comparison — `doc_11_chunk04`",
        "",
        "_One-call diagnostic. Not a pass rate. Source/schema/repaired prompt held fixed; provider is the controlled variable._",
        "",
        f"- chunk_sha256: `{bastion['chunk_sha256']}`",
        f"- baseline system_prompt_sha256: `{_BASELINE_PROMPT_SHA}`",
        f"- repaired system_prompt_sha256: `{_REPAIRED_PROMPT_SHA}`",
        f"- bastion product-prompt sha256: `{bastion['system_prompt_sha256']}`",
        f"- bastion adapter JSON-mode system sha256: `{call_meta['adapter_system_sha256']}`",
        f"- provider: `{call_meta['provider']}` · model: `{call_meta['model']}` · temperature: `{call_meta['extract_temperature']}`",
        f"- finish_reason: `{call_meta.get('finish_reason')}` · response_id: `{call_meta.get('response_id')}`",
        f"- tokens: prompt={call_meta['prompt_tokens']} "
        f"completion={call_meta['completion_tokens']} "
        f"total={call_meta['total_tokens']} "
        f"est_usd={call_meta['estimated_cost_usd']}",
        f"- built_at: `{call_meta['built_at']}`",
        "",
        "## Raw drafts (before gates)",
        "",
        "### Baseline (`gpt-4o-mini`, unrepaired prompt)",
        "",
        "```json",
        json.dumps(
            baseline.get("raw_drafts_before_gates")
            or [row["raw_draft"] for row in baseline.get("draft_trace") or []],
            indent=2,
        ),
        "```",
        "",
        "### Repaired mini (`gpt-4o-mini`)",
        "",
        "```json",
        json.dumps(repaired.get("raw_drafts_before_gates") or [], indent=2),
        "```",
        "",
        "### BastionGPT (repaired prompt, JSON-mode adapter)",
        "",
        "```json",
        json.dumps(bastion.get("raw_drafts_before_gates") or [], indent=2),
        "```",
        "",
        "## Deterministic dispositions",
        "",
        "### Baseline",
        "",
        "```json",
        json.dumps(_disp_rows(baseline), indent=2),
        "```",
        "",
        "### Repaired mini",
        "",
        "```json",
        json.dumps(_disp_rows(repaired), indent=2),
        "```",
        "",
        "### BastionGPT",
        "",
        "```json",
        json.dumps(_disp_rows(bastion), indent=2),
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
        "### Repaired mini",
        "",
        "```json",
        json.dumps(repaired.get("retained_after_postprocess") or [], indent=2),
        "```",
        "",
        "### BastionGPT",
        "",
        "```json",
        json.dumps(bastion.get("retained_after_postprocess") or [], indent=2),
        "```",
        "",
        "## Substantive outcomes vs TJ review (not a score)",
        "",
        "Identity reported separately; does not inflate substantive success.",
        "",
        "Fill after inspecting raw drafts, fact-level `grade`, and omitted classroom-strength / IEP / writing-math context.",
        "",
        "| Dimension | Outcome | Evidence |",
        "|---|---|---|",
        "| 1. Grade semantics | _pending_ | no `grade` predicate and no fact-level `grade=10` from “Math 10.” |",
        "| 2. IEP status | _pending_ | preserve active-IEP evidence TJ accepted for this slice |",
        "| 3. Classroom strength | _pending_ | effort/helpfulness survives; not attendance; not silently lost |",
        "| 4. Written expression | _pending_ | `written_expression` plus task + accuracy in `value_text` |",
        "| 5. Math performance | _pending_ | defensible math predicate; equation task + accuracy/trials preserved |",
        "| 6. Coverage | _pending_ | material writing baseline/goal/progress and math/algebraic-thinking evidence |",
        "| 7. Support | _pending_ | no new unsupported substantive facts or metadata |",
        "",
    ]
    path = out_dir / "comparison.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    load_dotenv(_WEEK1 / ".env")

    baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
    repaired = json.loads(_REPAIRED.read_text(encoding="utf-8"))
    if baseline.get("chunk_sha256") != _EXPECTED_CHUNK_SHA:
        raise SystemExit(f"baseline chunk SHA mismatch: {baseline.get('chunk_sha256')}")
    if baseline.get("system_prompt_sha256") != _BASELINE_PROMPT_SHA:
        raise SystemExit("baseline prompt SHA mismatch — refuse to compare against drifted artifact")
    if repaired.get("chunk_sha256") != _EXPECTED_CHUNK_SHA:
        raise SystemExit(f"repaired chunk SHA mismatch: {repaired.get('chunk_sha256')}")
    if repaired.get("system_prompt_sha256") != _REPAIRED_PROMPT_SHA:
        raise SystemExit("repaired prompt SHA mismatch — refuse to compare against drifted artifact")

    payload = baseline["user_payload"]
    source_blob = payload["source"]
    content = source_blob["content"]
    if _sha256_text(content) != _EXPECTED_CHUNK_SHA:
        raise SystemExit("retained user_payload content SHA mismatch")

    source = Source.model_validate({**source_blob, "content": content})
    child, _, _ = load_case_manifest(_MANIFEST)

    import extract as extract_mod

    extract_mod._PROMPT_TEMPLATE = (_WEEK1 / "extract_prompt.md").read_text(encoding="utf-8")
    system_prompt = extract_mod.build_extract_system_prompt()
    extract_mod.EXTRACT_SYSTEM_PROMPT = system_prompt
    product_prompt_sha = _sha256_text(system_prompt)
    if product_prompt_sha != _REPAIRED_PROMPT_SHA:
        raise SystemExit(
            f"current extract prompt drifted from repaired SHA: {product_prompt_sha}"
        )
    adapter_system = json_mode_system(system_prompt, SourceExtraction)

    provider = ModelProvider(backend="bastion")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _OUT_DIR / f"replay-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)

    try:
        result = provider.complete_structured(
            model=BASTION_MODEL,
            system=system_prompt,
            user=_extraction_user_payload(source),
            schema=SourceExtraction,
            temperature=EXTRACT_TEMPERATURE,
            max_tokens=BASTION_DEFAULT_MAX_TOKENS,
        )
    except BastionAccessError as exc:
        (out_dir / "access_not_live.json").write_text(
            json.dumps({"error": str(exc), "built_at": stamp}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "access_not_live", "error": str(exc)}))
        raise SystemExit(2) from exc
    except BastionParseError as exc:
        raw_path = out_dir / "raw_response.txt"
        raw_path.write_text(exc.raw_text, encoding="utf-8")
        meta = {
            "built_at": stamp,
            "provider": "bastion",
            "model": BASTION_MODEL,
            "extract_temperature": EXTRACT_TEMPERATURE,
            "finish_reason": exc.finish_reason,
            "response_id": exc.response_id,
            "prompt_tokens": exc.prompt_tokens,
            "completion_tokens": exc.completion_tokens,
            "total_tokens": exc.total_tokens,
            "system_prompt_sha256": product_prompt_sha,
            "adapter_system_sha256": _sha256_text(adapter_system),
            "chunk_sha256": _EXPECTED_CHUNK_SHA,
            "parse_error": str(exc),
            "raw_response": str(raw_path.relative_to(_WEEK1)),
        }
        (out_dir / "run_meta.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({"status": "parse_failed", **meta}, indent=2))
        raise SystemExit(3) from exc

    assert isinstance(result.data, SourceExtraction)
    drafts = list(result.data.facts)

    processed = _process_chunk_drafts(
        source=source,
        chunk_index=int(baseline["chunk_index"]),
        chunk_count=int(baseline["chunk_count"]),
        chunk_text=content,
        drafts=drafts,
        child=child,
    )
    processed["system_prompt_sha256"] = product_prompt_sha
    processed["adapter_system_sha256"] = _sha256_text(adapter_system)
    processed["user_payload"] = json.loads(_extraction_user_payload(source))
    processed["raw_drafts_before_gates"] = [d.model_dump(mode="json") for d in drafts]
    processed["model"] = BASTION_MODEL
    processed["provider"] = "bastion"
    processed["prompt_tokens"] = result.prompt_tokens
    processed["completion_tokens"] = result.completion_tokens
    processed["total_tokens"] = result.total_tokens
    processed["finish_reason"] = result.finish_reason
    processed["response_id"] = result.response_id
    processed["origin"] = "bastion_one_chunk_replay"
    processed["baseline_artifact"] = "evals/history/extraction_audit/doc_11_chunk04.json"
    processed["repaired_mini_artifact"] = str(_REPAIRED.relative_to(_WEEK1))
    processed["baseline_system_prompt_sha256"] = _BASELINE_PROMPT_SHA
    processed["repaired_system_prompt_sha256"] = _REPAIRED_PROMPT_SHA
    processed["extract_temperature"] = EXTRACT_TEMPERATURE
    processed["estimated_cost_usd"] = None
    processed["raw_text"] = result.raw_text

    if processed["chunk_sha256"] != _EXPECTED_CHUNK_SHA:
        raise SystemExit("replay chunk SHA drifted from baseline")

    artifact_path = out_dir / "doc_11_chunk04.json"
    artifact_path.write_text(json.dumps(processed, indent=2) + "\n", encoding="utf-8")
    if result.raw_text:
        (out_dir / "raw_response.txt").write_text(result.raw_text, encoding="utf-8")

    call_meta = {
        "built_at": stamp,
        "provider": "bastion",
        "model": BASTION_MODEL,
        "extract_temperature": EXTRACT_TEMPERATURE,
        "finish_reason": result.finish_reason,
        "response_id": result.response_id,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
        "estimated_cost_usd": None,
        "system_prompt_sha256": product_prompt_sha,
        "adapter_system_sha256": processed["adapter_system_sha256"],
        "baseline_system_prompt_sha256": _BASELINE_PROMPT_SHA,
        "repaired_system_prompt_sha256": _REPAIRED_PROMPT_SHA,
        "chunk_sha256": processed["chunk_sha256"],
        "artifact": str(artifact_path.relative_to(_WEEK1)),
    }
    (out_dir / "run_meta.json").write_text(
        json.dumps(call_meta, indent=2) + "\n", encoding="utf-8"
    )
    comparison = _write_comparison(
        out_dir=out_dir,
        baseline=baseline,
        repaired=repaired,
        bastion=processed,
        call_meta=call_meta,
    )
    latest = {
        "replay_dir": str(out_dir.relative_to(_WEEK1)),
        "artifact": str(artifact_path.relative_to(_WEEK1)),
        "comparison": str(comparison.relative_to(_WEEK1)),
        "chunk_sha256": processed["chunk_sha256"],
        "system_prompt_sha256": product_prompt_sha,
        "adapter_system_sha256": processed["adapter_system_sha256"],
        "artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
    }
    (_OUT_DIR / "LATEST.json").write_text(
        json.dumps(latest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(latest, indent=2))
    print(
        f"drafts={len(drafts)} tokens={result.total_tokens} "
        f"finish={result.finish_reason} "
        f"prompt_sha={product_prompt_sha[:12]}…"
    )


if __name__ == "__main__":
    main()
