"""Eval-only: audit extraction model output before deterministic gates.

Replays only the normal ``split_source_content`` chunks that contain the
sampled History evidence failures (plus known-good controls in those chunks).
Does not modify production ``extract.py``. Writes local artifacts under
``evals/history/extraction_audit/``.

This is a **replay**, not a recovery of the original 2026-08-10 full-fixture
generations, unless a prior Langfuse export is supplied via
``EXTRACTION_AUDIT_LANGFUSE_DIR``.
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

from extract import (  # noqa: E402
    EXTRACT_CHUNK_CHAR_LIMIT,
    EXTRACT_SYSTEM_PROMPT,
    _draft_is_skippable,
    _extraction_user_payload,
    _finalize_assertion,
    _finalize_as_of_date,
    _finalize_subject,
    _is_garbage_dob,
    _is_placeholder_value,
    _is_spurious_academic_behavioral_concern,
    _is_spurious_age_years,
    _is_spurious_attendance,
    _is_spurious_developmental_history,
    _is_spurious_grade,
    _is_spurious_health_plan_status,
    _is_spurious_iep_status,
    _is_spurious_sleep,
    _resolve_predicate_name,
    consolidate_medications_facts,
    dedupe_facts,
    draft_to_fact,
    extract_source_facts,
    fact_id_for_source,
    split_source_content,
)
from normalize import normalize_qualifier, normalize_value  # noqa: E402
from provider import EXTRACT_TEMPERATURE, ModelProvider, compute_cost_usd  # noqa: E402
from schemas import Child, ExtractedFactDraft, Fact, Ledger, Source  # noqa: E402
from test_all_stages import load_case_manifest  # noqa: E402

_OUT = _WEEK1 / "evals" / "history" / "extraction_audit"
_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_MANIFEST = _WEEK1 / "fixtures" / "fixture_001" / "manifest.json"

# Exact passages that identify the audit sample (substring match inside normal chunks).
AUDIT_TARGETS: list[dict[str, Any]] = [
    {
        "claim_id": "doc11_adaptive_not_reading",
        "source_id": "doc_11",
        "final_fact_id": "f_doc_11_012",
        "passage_needle": "adap ve and does not impede her learning",
        "expected_distinction": (
            "Adaptive behavior that does not impede learning is not reading."
        ),
        "role": "defect_sample",
        "match_any": [
            "does not impede her learning",
            "adap ve and does not impede",
            "adaptive and does not impede",
        ],
    },
    {
        "claim_id": "doc11_rad_adhd_not_trauma",
        "source_id": "doc_11",
        "final_fact_id": "f_doc_11_014",
        "passage_needle": "She has RAD and ADHD",
        "expected_distinction": (
            "RAD and ADHD diagnoses alone are not trauma narrative."
        ),
        "role": "defect_sample",
    },
    {
        "claim_id": "doc11_paragraph_not_reading",
        "source_id": "doc_11",
        "final_fact_id": "f_doc_11_017",
        "passage_needle": "approximate 5th grade",
        "expected_distinction": (
            "Writing a paragraph at an approximate grade level is written "
            "expression, not reading."
        ),
        "role": "defect_sample",
        "match_any": [
            "approximate 5th grade",
            "supporting sentences at an approximate",
            "write a paragraph",
        ],
    },
    {
        "claim_id": "doc25_form_not_eligible",
        "source_id": "doc_25",
        "final_fact_id": "f_doc_25_006",
        "passage_needle": "Not Eligible for Special Education   Exiting from Special Education",
        "expected_distinction": (
            "Unmarked “Not Eligible / Exiting” form options are not an actual "
            "IEP status determination."
        ),
        "role": "defect_sample",
    },
    {
        "claim_id": "doc25_supports_not_meds",
        "source_id": "doc_25",
        "final_fact_id": "f_doc_25_016",
        "passage_needle": "SUPPLEMENTARY AIDS & SERVICES AND OTHER SUPPORTS",
        "expected_distinction": (
            "A determination that other school supports are not needed is not "
            "medication evidence."
        ),
        "role": "defect_sample",
        "match_any": [
            "other supports for school personnel",
            "supports for school personnel",
            "are not needed",
            "SUPPLEMENTARY AIDS",
        ],
    },
    {
        "claim_id": "doc25_adoption_not_trauma",
        "source_id": "doc_25",
        "final_fact_id": "f_doc_25_019",
        "passage_needle": "adopted at 19 months so information on birth is limited",
        "expected_distinction": (
            "Adoption at 19 months, without trauma language in that claim, is "
            "not itself trauma history."
        ),
        "role": "defect_sample",
    },
    {
        "claim_id": "doc26_checklist_not_family_hx",
        "source_id": "doc_26",
        "final_fact_id": "f_doc_26_008",
        "passage_needle": "History of trauma (including abuse, neglect, molest, or domestic violence)",
        "expected_distinction": (
            "A checklist statement of suspected neglect/trauma concerns the "
            "child, not family medical/psychological history."
        ),
        "role": "defect_sample",
        "match_any": [
            "History of trauma (including abuse",
            "neglect, trauma suspected",
            "of neglect, trauma suspected",
        ],
    },
    {
        "claim_id": "doc26_no_meds_allergies_not_ihp",
        "source_id": "doc_26",
        "final_fact_id": "f_doc_26_010",
        "passage_needle": "No medications or allergies",
        "expected_distinction": (
            "“No medications or allergies” denies those topics, not an "
            "individual health-plan status."
        ),
        "role": "defect_sample",
        "match_any": [
            "No medications or allergies",
            "medications or allergies",
        ],
    },
    # Known-good controls (same selected chunks).
    {
        "claim_id": "control_doc25_milestone_walk",
        "source_id": "doc_25",
        "final_fact_id": None,
        "passage_needle": "walking at about 19 mos",
        "expected_distinction": "Correct developmental milestone (walking age).",
        "role": "control_good",
        "expect_predicate_in": {"walked_age_months", "developmental_history"},
        "match_any": ["walking at about 19 mos", "walking at about 19"],
    },
    {
        "claim_id": "control_doc25_medications",
        "source_id": "doc_25",
        "final_fact_id": None,
        "passage_needle": "1mg of guanfacine",
        "expected_distinction": "Correct medication list from the health narrative.",
        "role": "control_good",
        "expect_predicate_in": {"medications"},
        "match_any": ["guanfacine", "melatonin at night"],
    },
    {
        "claim_id": "control_doc26_sleep",
        "source_id": "doc_26",
        "final_fact_id": None,
        "passage_needle": "sleeps well from 8",
        "expected_distinction": "Correct sleep-pattern claim.",
        "role": "control_good",
        "expect_predicate_in": {"sleep"},
    },
    {
        "claim_id": "control_doc11_medications",
        "source_id": "doc_11",
        "final_fact_id": None,
        "passage_needle": "Geodon, Trileptal, and Vyvance",
        "expected_distinction": "Correct medication list near the RAD/ADHD sentence.",
        "role": "control_good",
        "expect_predicate_in": {"medications"},
    },
]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _skip_reason(draft: ExtractedFactDraft, source: Source) -> str | None:
    """Mirror ``_draft_is_skippable`` with an explicit reason string (eval-only)."""

    raw = (draft.value or "").strip()
    if not raw or raw.lower() in {"null", "none-stated", "n/a", "undefined"}:
        return "empty_or_nullish_value"
    if _is_placeholder_value(draft):
        return "placeholder_value"
    predicate = _resolve_predicate_name(draft)
    if predicate == "dob" and _is_garbage_dob(draft, source):
        return "garbage_dob"
    if predicate == "age_years" and _is_spurious_age_years(draft, source):
        return "spurious_age_years"
    if predicate == "grade" and _is_spurious_grade(draft, source):
        return "spurious_grade"
    if predicate == "iep_status" and _is_spurious_iep_status(draft, source):
        return "spurious_iep_status"
    if predicate == "attendance" and _is_spurious_attendance(draft):
        return "spurious_attendance"
    if predicate == "developmental_history" and _is_spurious_developmental_history(draft):
        return "spurious_developmental_history"
    if predicate == "behavioral_concern" and _is_spurious_academic_behavioral_concern(
        draft
    ):
        return "spurious_academic_behavioral_concern"
    if predicate == "health_plan_status" and _is_spurious_health_plan_status(draft):
        return "spurious_health_plan_status"
    if predicate == "sleep" and _is_spurious_sleep(draft):
        return "spurious_sleep"
    # Consistency check against public API.
    if _draft_is_skippable(draft, source):
        return "skippable_unclassified"
    return None


def _draft_public(draft: ExtractedFactDraft) -> dict[str, Any]:
    return draft.model_dump(mode="json")


def _match_final_fact(ledger: Ledger, fact_id: str | None) -> dict | None:
    if not fact_id:
        return None
    for f in ledger.facts:
        if f.id == fact_id:
            return f.model_dump(mode="json")
    return None


def _find_chunks_for_source(
    source: Source, needles: list[str]
) -> list[tuple[int, str, list[str]]]:
    chunks = split_source_content(source.content, limit=EXTRACT_CHUNK_CHAR_LIMIT)
    selected: list[tuple[int, str, list[str]]] = []
    for idx, chunk in enumerate(chunks):
        hits = [n for n in needles if n.lower() in chunk.lower()]
        if hits:
            selected.append((idx, chunk, hits))
    return selected


def _process_chunk_drafts(
    *,
    source: Source,
    chunk_index: int,
    chunk_count: int,
    chunk_text: str,
    drafts: list[ExtractedFactDraft],
    child: Child,
) -> dict[str, Any]:
    chunk_source = source.model_copy(update={"content": chunk_text})
    rows: list[dict[str, Any]] = []
    retained: list[Fact] = []
    for draft in drafts:
        pred = _resolve_predicate_name(draft)
        skip = _skip_reason(draft, source)
        row: dict[str, Any] = {
            "raw_draft": _draft_public(draft),
            "resolved_predicate": pred,
            "proposed_predicate": draft.proposed_predicate,
            "skipped": skip is not None,
            "skip_reason": skip,
            "normalized_value": None,
            "finalized_assertion": None,
            "finalized_reporter": None,
            "finalized_source_section": None,
            "finalized_as_of_date": None,
            "finalized_subject": None,
            "retained_fact_id": None,
            "draft_to_fact_error": None,
        }
        if skip is None:
            try:
                # Provisional id; renumbered after dedupe/consolidation below.
                fact = draft_to_fact(
                    draft,
                    fact_id=fact_id_for_source(source.id, len(retained) + 1),
                    source=source,
                    child=child,
                )
                retained.append(fact)
                row["normalized_value"] = fact.value
                row["finalized_assertion"] = fact.assertion
                row["finalized_reporter"] = fact.reporter
                row["finalized_source_section"] = fact.source_section
                row["finalized_as_of_date"] = fact.as_of_date
                row["finalized_subject"] = fact.subject
                row["retained_fact_id"] = fact.id
            except ValueError as exc:
                row["skipped"] = True
                row["skip_reason"] = "draft_to_fact_value_error"
                row["draft_to_fact_error"] = str(exc)
        else:
            # Still record what normalize would have produced for inspection.
            try:
                row["normalized_value"] = normalize_value(
                    pred, draft.value or "", draft.value_text or ""
                )
                row["finalized_assertion"] = _finalize_assertion(
                    draft, predicate=pred, value=row["normalized_value"] or ""
                )
                row["finalized_reporter"] = (
                    draft.reporter.strip()
                    if draft.reporter and draft.reporter.strip()
                    else None
                )
                row["finalized_source_section"] = (
                    draft.source_section.strip()
                    if draft.source_section and draft.source_section.strip()
                    else None
                )
                row["finalized_as_of_date"] = _finalize_as_of_date(draft, source)
                row["finalized_subject"] = _finalize_subject(draft, source, pred)
                row["normalized_qualifier"] = normalize_qualifier(draft.qualifier)
            except Exception as exc:  # noqa: BLE001 — audit must continue
                row["normalize_error"] = str(exc)
        rows.append(row)

    before_dedupe = list(retained)
    after_dedupe = dedupe_facts(before_dedupe)
    after_meds = consolidate_medications_facts(after_dedupe)
    after_meds = [
        f.model_copy(update={"id": fact_id_for_source(source.id, i)})
        for i, f in enumerate(after_meds, start=1)
    ]

    removed_by_dedupe = [
        f.model_dump(mode="json")
        for f in before_dedupe
        if f.id not in {x.id for x in after_dedupe}
    ]
    # Medication consolidation may replace multiple with one — detect by count.
    med_before = [f for f in after_dedupe if f.predicate == "medications"]
    med_after = [f for f in after_meds if f.predicate == "medications"]

    return {
        "source_id": source.id,
        "source_label": source.label,
        "source_date": source.date,
        "chunk_index": chunk_index,
        "chunk_count": chunk_count,
        "chunk_sha256": _sha256_text(chunk_text),
        "chunk_char_len": len(chunk_text),
        "draft_trace": rows,
        "retained_before_dedupe": [f.model_dump(mode="json") for f in before_dedupe],
        "removed_by_dedupe": removed_by_dedupe,
        "medications_before_consolidation": [f.model_dump(mode="json") for f in med_before],
        "medications_after_consolidation": [f.model_dump(mode="json") for f in med_after],
        "retained_after_postprocess": [f.model_dump(mode="json") for f in after_meds],
        "user_payload_sha256": _sha256_text(_extraction_user_payload(chunk_source)),
        "system_prompt_sha256": _sha256_text(EXTRACT_SYSTEM_PROMPT),
    }


def _try_load_langfuse_dir() -> dict[str, Any] | None:
    """Optional pre-exported Langfuse payloads (eval-only; not fetched here)."""

    path = os.getenv("EXTRACTION_AUDIT_LANGFUSE_DIR")
    if not path:
        return None
    root = Path(path)
    if not root.is_dir():
        return None
    index = root / "index.json"
    if not index.exists():
        return None
    return json.loads(index.read_text(encoding="utf-8"))


def main() -> None:
    load_dotenv(_WEEK1 / ".env")
    _OUT.mkdir(parents=True, exist_ok=True)

    child, sources, _ = load_case_manifest(_MANIFEST)
    by_source = {s.id: s for s in sources}
    ledger = Ledger.model_validate(
        json.loads(_CACHE.read_text(encoding="utf-8"))["ledger"]
    )
    cache_meta = json.loads(_CACHE.read_text(encoding="utf-8"))

    # Group needles by source → unique chunks to call.
    needles_by_source: dict[str, list[str]] = {}
    for t in AUDIT_TARGETS:
        needles_by_source.setdefault(t["source_id"], []).append(t["passage_needle"])

    chunk_jobs: list[tuple[Source, int, int, str, list[str]]] = []
    for source_id, needles in needles_by_source.items():
        source = by_source[source_id]
        chunks = split_source_content(source.content, limit=EXTRACT_CHUNK_CHAR_LIMIT)
        selected = _find_chunks_for_source(source, needles)
        for idx, chunk_text, hits in selected:
            chunk_jobs.append((source, idx, len(chunks), chunk_text, hits))

    langfuse_export = _try_load_langfuse_dir()
    origin = "langfuse_export" if langfuse_export else "targeted_chunk_replay"
    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    provider = None
    if origin == "targeted_chunk_replay":
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY required for targeted chunk replay")
        provider = ModelProvider()

    run_meta = {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "origin": origin,
        "model": model,
        "extract_temperature": EXTRACT_TEMPERATURE,
        "system_prompt_sha256": _sha256_text(EXTRACT_SYSTEM_PROMPT),
        "chunk_limit": EXTRACT_CHUNK_CHAR_LIMIT,
        "fixture_cache_model": cache_meta.get("model"),
        "fixture_cache_built_at": cache_meta.get("built_at"),
        "note": (
            "Replay of selected normal split_source_content chunks. Not the "
            "original 2026-08-10 full-fixture response unless Langfuse export "
            "was supplied via EXTRACTION_AUDIT_LANGFUSE_DIR."
        ),
        "calls": [],
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    chunk_results: list[dict[str, Any]] = []

    for source, chunk_index, chunk_count, chunk_text, hits in chunk_jobs:
        chunk_source = source.model_copy(update={"content": chunk_text})
        user_payload = _extraction_user_payload(chunk_source)
        out_path = _OUT / f"{source.id}_chunk{chunk_index:02d}.json"
        call_rec: dict[str, Any] = {
            "source_id": source.id,
            "chunk_index": chunk_index,
            "chunk_count": chunk_count,
            "chunk_sha256": _sha256_text(chunk_text),
            "needle_hits": hits,
            "user_payload_sha256": _sha256_text(user_payload),
            "system_prompt_sha256": _sha256_text(EXTRACT_SYSTEM_PROMPT),
        }

        reuse = (
            os.getenv("EXTRACTION_AUDIT_REUSE_EXISTING", "1") == "1"
            and out_path.exists()
            and origin == "targeted_chunk_replay"
        )
        if reuse:
            processed = json.loads(out_path.read_text(encoding="utf-8"))
            if processed.get("chunk_sha256") != _sha256_text(chunk_text):
                reuse = False
            else:
                call_rec["reused_artifact"] = out_path.name
                call_rec["prompt_tokens"] = processed.get("prompt_tokens", 0)
                call_rec["completion_tokens"] = processed.get("completion_tokens", 0)
                call_rec["total_tokens"] = processed.get("total_tokens", 0)
                call_rec["model"] = processed.get("model", model)
                chunk_results.append(processed)
                run_meta["calls"].append(call_rec)
                print(f"reused {out_path.name}")
                continue

        if origin == "langfuse_export" and langfuse_export is not None:
            key = f"{source.id}:{chunk_index}"
            exported = langfuse_export.get("chunks", {}).get(key)
            if exported is None:
                call_rec["validation_failure"] = "missing_langfuse_chunk"
                run_meta["calls"].append(call_rec)
                continue
            drafts = [
                ExtractedFactDraft.model_validate(d) for d in exported["raw_drafts"]
            ]
            call_rec["prompt_tokens"] = exported.get("prompt_tokens", 0)
            call_rec["completion_tokens"] = exported.get("completion_tokens", 0)
            call_rec["total_tokens"] = exported.get("total_tokens", 0)
            call_rec["model"] = exported.get("model", model)
        else:
            assert provider is not None
            drafts, total, p_tok, c_tok = extract_source_facts(
                provider, child=child, source=chunk_source, model=model
            )
            call_rec["prompt_tokens"] = p_tok
            call_rec["completion_tokens"] = c_tok
            call_rec["total_tokens"] = total
            call_rec["model"] = model
            call_rec["estimated_cost_usd"] = compute_cost_usd(model, p_tok, c_tok)
            run_meta["total_prompt_tokens"] += p_tok
            run_meta["total_completion_tokens"] += c_tok
            run_meta["total_tokens"] += total
            run_meta["estimated_cost_usd"] += call_rec["estimated_cost_usd"]

        processed = _process_chunk_drafts(
            source=source,
            chunk_index=chunk_index,
            chunk_count=chunk_count,
            chunk_text=chunk_text,
            drafts=drafts,
            child=child,
        )
        processed["needle_hits"] = hits
        processed["model"] = call_rec["model"]
        processed["prompt_tokens"] = call_rec.get("prompt_tokens", 0)
        processed["completion_tokens"] = call_rec.get("completion_tokens", 0)
        processed["total_tokens"] = call_rec.get("total_tokens", 0)
        processed["origin"] = origin
        # Persist payload + raw drafts for local inspection (approved-anonymized).
        processed["user_payload"] = json.loads(user_payload)
        processed["raw_drafts_before_gates"] = [_draft_public(d) for d in drafts]
        chunk_results.append(processed)
        run_meta["calls"].append(call_rec)

        out_path.write_text(json.dumps(processed, indent=2) + "\n", encoding="utf-8")
        print(
            f"wrote {out_path.name} drafts={len(drafts)} "
            f"tokens={call_rec.get('total_tokens', 0)}"
        )

    # Claim-level matching: find raw drafts whose value_text overlaps the needle.
    def _blob_matches(blob: str, target: dict[str, Any]) -> bool:
        low = blob.lower()
        needles = list(target.get("match_any") or []) + [target["passage_needle"]]
        return any(n.lower() in low for n in needles if n)

    claim_rows: list[dict[str, Any]] = []
    for target in AUDIT_TARGETS:
        matched_raw: list[dict[str, Any]] = []
        matched_post: list[dict[str, Any]] = []
        chunk_refs: list[str] = []
        for cr in chunk_results:
            if cr["source_id"] != target["source_id"]:
                continue
            for trace in cr["draft_trace"]:
                draft = trace["raw_draft"]
                blob = f"{draft.get('value_text') or ''} {draft.get('value') or ''}"
                if _blob_matches(blob, target):
                    matched_raw.append(trace)
                    chunk_refs.append(
                        f"{cr['source_id']}_chunk{cr['chunk_index']:02d}"
                    )
            for fact in cr["retained_after_postprocess"]:
                blob = f"{fact.get('value_text') or ''} {fact.get('value') or ''}"
                if _blob_matches(blob, target):
                    matched_post.append(fact)

        # Also note whether the source chunk contains the passage even if omitted.
        passage_in_selected_chunks = False
        for cr in chunk_results:
            if cr["source_id"] != target["source_id"]:
                continue
            payload_content = (cr.get("user_payload") or {}).get("source", {}).get(
                "content", ""
            )
            if _blob_matches(payload_content, target):
                passage_in_selected_chunks = True
                chunk_refs.append(
                    f"{cr['source_id']}_chunk{cr['chunk_index']:02d}"
                )

        final = _match_final_fact(ledger, target.get("final_fact_id"))
        claim_rows.append(
            {
                "claim_id": target["claim_id"],
                "role": target["role"],
                "source_id": target["source_id"],
                "final_fact_id": target.get("final_fact_id"),
                "expected_distinction": target["expected_distinction"],
                "passage_needle": target["passage_needle"],
                "passage_present_in_selected_chunk": passage_in_selected_chunks,
                "chunk_artifacts": sorted(set(chunk_refs)),
                "raw_matches": matched_raw,
                "postprocess_retained_matches": matched_post,
                "final_ledger_fact": final,
                "unregistered_in_raw_matches": any(
                    (m.get("resolved_predicate") == "__unregistered__")
                    or (
                        str(m.get("raw_draft", {}).get("predicate", "")).find(
                            "unregistered"
                        )
                        >= 0
                    )
                    or (m.get("raw_draft", {}).get("proposed_predicate"))
                    for m in matched_raw
                ),
                "expect_predicate_in": sorted(target.get("expect_predicate_in") or []),
            }
        )

    summary = {
        "run": run_meta,
        "claims": claim_rows,
        "chunk_artifact_files": sorted(p.name for p in _OUT.glob("*_chunk*.json")),
    }
    (_OUT / "audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"origin={origin} calls={len(run_meta['calls'])} "
        f"tokens={run_meta['total_tokens']} "
        f"est_cost_usd={run_meta['estimated_cost_usd']:.4f}"
    )
    print(f"wrote {_OUT / 'audit_summary.json'}")


if __name__ == "__main__":
    main()
