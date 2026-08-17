"""Render readable per-item traces from existing extraction-audit artifacts.

No model calls. Uses approved-anonymized audit JSON already on disk.

Default scope is one small chunk (``doc_11_chunk04``) that includes both
retained facts and observed silent drops. Pass ``--all`` for every audit chunk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

_AUDIT = _WEEK1 / "evals" / "history" / "extraction_audit"
_CACHE = _WEEK1 / "evals" / "cache" / "fixture_001_ledger.json"
_OUT = _AUDIT / "item_comparison"

DEFAULT_CHUNK = "doc_11_chunk04.json"
DEFAULT_CHUNK_STEM = "doc_11_chunk04"
COMPARISON_PAGES = [
    "doc_11_chunk01",
    "doc_11_chunk02",
    "doc_11_chunk04",
    "doc_25_chunk00",
    "doc_25_chunk01",
    "doc_25_chunk02",
    "doc_25_chunk03",
    "doc_26_chunk00",
]

# Review prompts for the acceptance slice — questions, not approved labels.
SLICE_REVIEW_PROMPTS = {
    "doc_11_chunk04": [
        (
            "item 02",
            "course name interpreted as grade, then dropped — is the "
            "extraction wrong, the drop appropriate, or both?",
        ),
        (
            "item 03",
            "annual-review date interpreted as active IEP status — "
            "supported by source?",
        ),
        (
            "item 04",
            "classroom-strength evidence interpreted as attendance, then "
            "dropped — what evidence was lost?",
        ),
        (
            "item 05",
            "writing performance interpreted as basic_reading with value "
            "`5` — predicate and value both reviewable?",
        ),
        (
            "item 06",
            "retained math claim whose local supporting passage was not "
            "located — resolve against the full chunk below before deciding.",
        ),
    ]
}


class MissingChunkSourceError(RuntimeError):
    """Full source chunk text is not retained in the audit artifact."""


class ChunkShaMismatchError(RuntimeError):
    """Retained source text does not hash to the recorded chunk_sha256."""


def _norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_full_chunk_source(data: dict[str, Any], *, artifact_path: Path) -> str:
    """
    Load the exact retained chunk text and verify it matches chunk_sha256.

    Never substitutes another source or data zone.
    """

    recorded = data.get("chunk_sha256")
    if not recorded:
        raise MissingChunkSourceError(
            f"{artifact_path.name}: missing chunk_sha256 in audit artifact"
        )
    content = ((data.get("user_payload") or {}).get("source") or {}).get("content")
    if content is None or content == "":
        raise MissingChunkSourceError(
            f"{artifact_path.name}: full source chunk content not retained under "
            f"user_payload.source.content (recorded chunk_sha256={recorded}). "
            "Refusing to fall back to another source or data zone."
        )
    actual = sha256_text(content)
    if actual != recorded:
        raise ChunkShaMismatchError(
            f"{artifact_path.name}: retained content sha {actual} does not match "
            f"recorded chunk_sha256 {recorded}. Refusing silent substitution."
        )
    return content


def _find_passage(chunk_text: str, needle: str, *, radius: int = 180) -> str | None:
    """Locate a short source window; tolerate whitespace/newline differences."""

    if not chunk_text or not needle:
        return None
    raw = needle.strip()
    if not raw:
        return None

    def _window(idx: int, length: int) -> str:
        start = max(0, idx - radius)
        end = min(len(chunk_text), idx + length + radius)
        excerpt = chunk_text[start:end].replace("\n", " ").strip()
        excerpt = re.sub(r"\s+", " ", excerpt)
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(chunk_text) else ""
        return f"{prefix}{excerpt}{suffix}"

    idx = chunk_text.find(raw)
    if idx < 0:
        idx = chunk_text.lower().find(raw.lower())
    if idx >= 0:
        return _window(idx, len(raw))

    # Whitespace-tolerant: collapse runs of whitespace in both texts.
    def _collapse(s: str) -> tuple[str, list[int]]:
        out: list[str] = []
        index_map: list[int] = []
        prev_space = False
        for i, ch in enumerate(s):
            if ch.isspace():
                if not prev_space:
                    out.append(" ")
                    index_map.append(i)
                    prev_space = True
            else:
                out.append(ch)
                index_map.append(i)
                prev_space = False
        return "".join(out), index_map

    hay, hay_map = _collapse(chunk_text)
    needle_c, _ = _collapse(raw)
    if not needle_c.strip():
        return None
    pos = hay.lower().find(needle_c.lower())
    if pos < 0:
        # Short distinctive stub across whitespace.
        for length in (min(64, len(needle_c)), min(40, len(needle_c)), min(24, len(needle_c))):
            if length < 12:
                break
            stub = needle_c[:length]
            pos = hay.lower().find(stub.lower())
            if pos >= 0:
                needle_c = stub
                break
    if pos < 0:
        return None
    orig_idx = hay_map[pos]
    orig_len = hay_map[min(pos + len(needle_c) - 1, len(hay_map) - 1)] - orig_idx + 1
    return _window(orig_idx, orig_len)


def _load_ledger_facts() -> list[dict[str, Any]]:
    if not _CACHE.exists():
        return []
    payload = json.loads(_CACHE.read_text(encoding="utf-8"))
    ledger = payload.get("ledger") or payload
    return list(ledger.get("facts") or [])


def _match_legacy_fact(
    ledger_facts: list[dict[str, Any]],
    *,
    source_id: str,
    draft: dict[str, Any],
    local_fact: dict[str, Any] | None,
    retained_fact_id: str | None,
) -> tuple[dict[str, Any] | None, str]:
    vt = None
    if local_fact:
        vt = local_fact.get("value_text") or local_fact.get("value")
    if not vt:
        vt = draft.get("value_text") or draft.get("value")
    vt_norm = _norm(str(vt or ""))

    same_source = [
        f
        for f in ledger_facts
        if str(f.get("id") or "").startswith(f"f_{source_id}_")
        or (f.get("source_id") == source_id)
    ]
    if not same_source:
        same_source = [
            f for f in ledger_facts if str(f.get("id") or "").startswith(f"f_{source_id}_")
        ]

    if vt_norm:
        for f in same_source:
            cand = _norm(str(f.get("value_text") or f.get("value") or ""))
            if cand and (cand == vt_norm or vt_norm in cand or cand in vt_norm):
                return f, "value_text_match"

    if retained_fact_id:
        by_id = next((f for f in ledger_facts if f.get("id") == retained_fact_id), None)
        if by_id is not None:
            cand = _norm(str(by_id.get("value_text") or by_id.get("value") or ""))
            if (
                vt_norm
                and cand
                and cand != vt_norm
                and vt_norm not in cand
                and cand not in vt_norm
            ):
                return None, "fact_id_collision_different_content"
            return by_id, "fact_id_match"

    return None, "no_legacy_match"


def _disposition_row(trace: dict[str, Any]) -> dict[str, Any]:
    draft = trace.get("raw_draft") or {}
    if trace.get("skipped"):
        return {
            "kind": "observed_silent_drop",
            "label": "observed silent drop",
            "gate_or_check": "_draft_is_skippable",
            "reason": trace.get("skip_reason") or "extract_gate_skippable",
            "fact_id": None,
            "before": {"value": draft.get("value")},
            "after": None,
        }
    before = draft.get("value")
    after = trace.get("normalized_value")
    fact_id = trace.get("retained_fact_id")
    if after is not None and str(after) != str(before):
        return {
            "kind": "transformed",
            "label": "transformed",
            "gate_or_check": "normalize_value",
            "reason": "normalize_value",
            "fact_id": fact_id,
            "before": {"value": before},
            "after": {"value": after},
        }
    if fact_id:
        return {
            "kind": "retained",
            "label": "retained",
            "gate_or_check": None,
            "reason": None,
            "fact_id": fact_id,
            "before": None,
            "after": None,
        }
    return {
        "kind": "observed_silent_drop",
        "label": "observed silent drop",
        "gate_or_check": "postprocess_omission_without_skip_flag",
        "reason": "retained_raw_missing_after_postprocess",
        "fact_id": None,
        "before": None,
        "after": None,
    }


def _fmt_fact(fact: dict[str, Any] | None) -> str:
    if not fact:
        return "_none_"
    pred = fact.get("predicate")
    return (
        f"`{fact.get('id')}` · predicate=`{pred}` · value=`{fact.get('value')}` · "
        f"value_text={json.dumps(fact.get('value_text'), ensure_ascii=False)} · "
        f"assertion=`{fact.get('assertion')}` · reporter=`{fact.get('reporter')}` · "
        f"as_of_date=`{fact.get('as_of_date')}`"
    )


def _fmt_item_review(
    latest: Any,
    history: list[Any],
    *,
    invalidated_count: int = 0,
) -> list[str]:
    lines = ["### 5. Human item review (append-only)", ""]
    if latest is None:
        lines.append("_No human item review recorded yet._")
        if invalidated_count:
            lines.append(
                f"_({invalidated_count} invalidated test/demo row(s) exist in the "
                "append-only log and are not current review state.)_"
            )
        lines.append("")
        return lines
    j = latest.judgments
    lines += [
        f"- **latest human** · origin=`{latest.origin}` · "
        f"reviewer=`{latest.reviewer_id}`/`{latest.reviewer_role}` · "
        f"at `{latest.reviewed_at}`",
        f"- source_support: **{j.source_support}**",
        f"- predicate: **{j.predicate}**",
        f"- value: **{j.value}**",
        f"- metadata: **{j.metadata}**",
        f"- deterministic_disposition: **{j.deterministic_disposition}**",
    ]
    if latest.notes:
        lines.append(f"- notes: {latest.notes}")
    if len(history) > 1:
        lines.append("")
        lines.append(f"_Prior human judgments retained in log ({len(history)} total):_")
        for prior in history[:-1]:
            lines.append(
                f"- `{prior.reviewed_at}` · {prior.origin}/{prior.reviewer_id} · "
                f"support={prior.judgments.source_support} "
                f"pred={prior.judgments.predicate} val={prior.judgments.value}"
            )
    if invalidated_count:
        lines.append(
            f"_Also: {invalidated_count} invalidated test/demo row(s) for this "
            "item are preserved in the log but do not count as review._"
        )
    lines.append("")
    return lines


def render_chunk(
    chunk_path: Path,
    *,
    ledger_facts: list[dict[str, Any]],
    item_reviews_by_id: dict[str, list[Any]] | None = None,
    coverage_for_chunk: list[Any] | None = None,
    invalidated_item_shas: set[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    data = json.loads(chunk_path.read_text(encoding="utf-8"))
    chunk_text = load_full_chunk_source(data, artifact_path=chunk_path)
    recorded_sha = data["chunk_sha256"]
    retained_local = {
        f.get("id"): f for f in (data.get("retained_after_postprocess") or []) if f.get("id")
    }
    source_id = str(data.get("source_id") or "")
    stem = chunk_path.stem
    item_reviews_by_id = item_reviews_by_id or {}
    coverage_for_chunk = coverage_for_chunk or []
    invalidated_item_shas = invalidated_item_shas or set()

    lines: list[str] = [
        f"# Item comparison — `{stem}`",
        "",
        "_Diagnostic render from existing targeted-chunk replay artifacts. "
        "No new model calls. Chunk-local facts are the trustworthy retained "
        "row for this replay. Legacy-cache rows are matched by value_text "
        "(not fact id) because the 77-fact cache is `legacy_untraceable` and "
        "ids collide across runs._",
        "",
        f"- source: `{data.get('source_id')}` · {data.get('source_label')}",
        f"- source_date: `{data.get('source_date')}`",
        f"- chunk: `{data.get('chunk_index')}` / `{data.get('chunk_count')}`",
        f"- chunk_sha256: `{recorded_sha}`",
        f"- model: `{data.get('model')}` · origin: `{data.get('origin')}`",
        f"- raw items: **{len(data.get('draft_trace') or [])}**",
        "",
        "## Legend",
        "",
        "| Stage | Meaning |",
        "|---|---|",
        "| Complete source chunk | Full chunk text for **omission / recall** review |",
        "| Source passage | Local excerpt around one model-produced item |",
        "| Raw extraction | Model draft before `_draft_is_skippable` |",
        "| Transformation / drop | Deterministic disposition in this replay |",
        "| Chunk-local fact | Fact after normalize/`draft_to_fact` in this chunk |",
        "| Legacy ledger fact | Same-content row in the 77-fact cache, if found |",
        "| Human item review | Append-only judgments; latest shown, history kept |",
        "",
    ]

    prompts = SLICE_REVIEW_PROMPTS.get(stem)
    if prompts:
        lines += [
            "## Review prompts for this slice (not pre-decided labels)",
            "",
        ]
        for label, text in prompts:
            lines.append(f"- **{label}:** {text}")
        lines.append("")

    lines += [
        "## Complete source chunk (omission surface)",
        "",
        f"_This is the full retained source for `chunk_sha256={recorded_sha}`. "
        "Use it to identify evidence the model never extracted. Item-local "
        "excerpts below cannot expose omissions on their own._",
        "",
        f"**chunk_sha256:** `{recorded_sha}`",
        "",
        "```text",
        chunk_text,
        "```",
        "",
    ]

    if coverage_for_chunk:
        lines += ["## Recorded human coverage omissions", ""]
        for o in coverage_for_chunk:
            pred = ""
            if o.proposed_predicate:
                flag = (
                    "provisional"
                    if o.proposed_predicate_provisional
                    else "non-provisional"
                )
                pred = f" · proposed_predicate=`{o.proposed_predicate}` ({flag})"
            lines.append(
                f"- {o.description} · locator={json.dumps(o.source_locator)}"
                f"{pred} · {o.reviewer_id}/{o.origin} @ {o.reviewed_at}"
            )
        lines.append("")
    else:
        lines += [
            "## Recorded human coverage omissions",
            "",
            "_None recorded yet. Use the complete source chunk above to find omissions._",
            "",
        ]

    lines += ["## Items", ""]

    machine_items: list[dict[str, Any]] = []
    for idx, trace in enumerate(data.get("draft_trace") or []):
        draft = trace.get("raw_draft") or {}
        disp = _disposition_row(trace)
        needle = draft.get("value_text") or draft.get("value") or ""
        passage = _find_passage(chunk_text, str(needle))
        fact_id = disp.get("fact_id")
        local_fact = retained_local.get(fact_id) if fact_id else None
        ledger_fact, legacy_match = _match_legacy_fact(
            ledger_facts,
            source_id=source_id,
            draft=draft,
            local_fact=local_fact,
            retained_fact_id=fact_id,
        )

        item_id = (
            f"{data.get('source_id')}:chunk:{recorded_sha[:12]}"
            f":raw:{idx:03d}"
        )
        from evals.history.item_review import record_content_sha

        all_for_item = item_reviews_by_id.get(item_id, [])
        invalidated_for_item = [
            r for r in all_for_item if record_content_sha(r) in invalidated_item_shas
        ]
        human_history = [
            r
            for r in all_for_item
            if record_content_sha(r) not in invalidated_item_shas and r.origin == "human"
        ]
        latest = human_history[-1] if human_history else None

        lines += [
            f"## Item {idx:02d} — `{item_id}`",
            "",
            "### 1. Source passage (item-local excerpt)",
            "",
        ]
        if passage:
            lines.append(f"> {passage}")
        else:
            lines += [
                "> ⚠️ **Passage not located in the full chunk text.**",
                ">",
                f"> Needle: {json.dumps(str(needle)[:160], ensure_ascii=False)}",
                ">",
                "> This is a human-review question — not an automatic "
                "hallucination label. Resolve against the complete source "
                "chunk above before deciding.",
            ]
        lines += [
            "",
            "### 2. Raw model extraction",
            "",
            f"- predicate: `{draft.get('predicate')}`",
            f"- value: `{draft.get('value')}`",
            f"- value_text: {json.dumps(draft.get('value_text'), ensure_ascii=False)}",
            f"- assertion: `{draft.get('assertion')}` · reporter: `{draft.get('reporter')}`",
            f"- life_stage: `{draft.get('life_stage')}` · as_of_date: `{draft.get('as_of_date')}`",
            f"- confidence: `{draft.get('confidence')}` · valence: `{draft.get('valence')}`",
            "",
            "### 3. Transformation / drop",
            "",
            f"- disposition: **{disp['label']}** (`{disp['kind']}`)",
        ]
        if disp.get("gate_or_check"):
            lines.append(f"- gate/check: `{disp['gate_or_check']}`")
        if disp.get("reason"):
            lines.append(f"- reason: `{disp['reason']}`")
        if disp.get("before") or disp.get("after"):
            lines.append(
                f"- before→after value: `{disp.get('before')}` → `{disp.get('after')}`"
            )
        lines += [
            "",
            "### 4. Ledger / retained fact",
            "",
            f"- chunk-local: {_fmt_fact(local_fact)}",
            f"- legacy cache ({legacy_match}): {_fmt_fact(ledger_fact)}",
            "",
        ]
        lines += _fmt_item_review(
            latest,
            human_history,
            invalidated_count=len(invalidated_for_item),
        )

        machine_items.append(
            {
                "item_id": item_id,
                "index": idx,
                "source_passage": passage,
                "passage_located": passage is not None,
                "raw_draft": draft,
                "disposition": disp,
                "chunk_local_fact": local_fact,
                "legacy_match": legacy_match,
                "legacy_ledger_fact": {
                    "id": ledger_fact.get("id"),
                    "predicate": ledger_fact.get("predicate"),
                    "value": ledger_fact.get("value"),
                    "value_text": ledger_fact.get("value_text"),
                    "assertion": ledger_fact.get("assertion"),
                    "as_of_date": ledger_fact.get("as_of_date"),
                    "reporter": ledger_fact.get("reporter"),
                }
                if ledger_fact
                else None,
                "latest_human_item_review": latest.model_dump(mode="json")
                if latest
                else None,
                "invalidated_review_count": len(invalidated_for_item),
            }
        )

    machine = {
        "source_id": data.get("source_id"),
        "chunk_index": data.get("chunk_index"),
        "chunk_sha256": recorded_sha,
        "chunk_content_sha256_verified": True,
        "model": data.get("model"),
        "origin": data.get("origin"),
        "artifact_file": chunk_path.name,
        "items": machine_items,
        "counts": {
            "raw_items": len(machine_items),
            "retained": sum(
                1 for i in machine_items if i["disposition"]["kind"] == "retained"
            ),
            "transformed": sum(
                1 for i in machine_items if i["disposition"]["kind"] == "transformed"
            ),
            "observed_silent_drop": sum(
                1
                for i in machine_items
                if i["disposition"]["kind"] == "observed_silent_drop"
            ),
            "passage_not_located": sum(
                1 for i in machine_items if not i["passage_located"]
            ),
        },
    }
    return "\n".join(lines).rstrip() + "\n", machine


def render_all_comparisons(
    *,
    store: Any | None = None,
    run_id: str | None = None,
    artifact_id: str | None = None,
) -> list[dict[str, Any]]:
    """Render all eight comparison pages; optionally overlay human item/coverage reviews."""

    from evals.history.item_review import (
        invalidated_sha_set,
        load_coverage_reviews,
        load_item_reviews,
        record_content_sha,
    )

    _OUT.mkdir(parents=True, exist_ok=True)
    ledger_facts = _load_ledger_facts()

    item_by_id: dict[str, list[Any]] = {}
    coverage_by_chunk: dict[str, list[Any]] = {}
    inv_item: set[str] = set()
    inv_cov: set[str] = set()
    if store is not None and run_id is not None:
        inv_item = invalidated_sha_set(store, run_id, kind="item_review")
        inv_cov = invalidated_sha_set(store, run_id, kind="coverage_review")
        for rec in load_item_reviews(store, run_id):
            if artifact_id and rec.artifact_id != artifact_id:
                continue
            item_by_id.setdefault(rec.item_id, []).append(rec)
        for cov in load_coverage_reviews(store, run_id):
            if artifact_id and cov.artifact_id != artifact_id:
                continue
            if record_content_sha(cov) in inv_cov:
                continue
            if cov.origin != "human":
                continue
            coverage_by_chunk.setdefault(cov.chunk_sha256, []).append(cov)

    machines: list[dict[str, Any]] = []
    index_lines = [
        "# Extraction item comparisons",
        "",
        "_Generated from existing audit replay artifacts — no new model calls._",
        "",
        "- Origin: `targeted_chunk_replay`",
        "- Not the original 2026-08-10 Langfuse generations",
        "- Not the parent of the legacy 77-fact cache",
        "- Extraction content remains unreviewed at the artifact level until a "
        "human records an artifact decision",
        "",
        "**Start here** for the small 7-item slice:",
        f"- [`{DEFAULT_CHUNK_STEM}.md`]({DEFAULT_CHUNK_STEM}.md)",
        "",
        "- [Extraction review summary](extraction_review_summary.md)",
        "",
        "All chunks:",
        "",
    ]
    for stem in COMPARISON_PAGES:
        path = _AUDIT / f"{stem}.json"
        if not path.exists():
            raise MissingChunkSourceError(f"missing audit artifact: {path}")
        data_preview = json.loads(path.read_text(encoding="utf-8"))
        chunk_sha = data_preview["chunk_sha256"]
        md, machine = render_chunk(
            path,
            ledger_facts=ledger_facts,
            item_reviews_by_id=item_by_id,
            coverage_for_chunk=coverage_by_chunk.get(chunk_sha, []),
            invalidated_item_shas=inv_item,
        )
        (_OUT / f"{stem}.md").write_text(md, encoding="utf-8")
        (_OUT / f"{stem}.json").write_text(
            json.dumps(machine, indent=2) + "\n", encoding="utf-8"
        )
        c = machine["counts"]
        index_lines.append(
            f"- [`{stem}.md`]({stem}.md) — raw={c['raw_items']} "
            f"retained={c['retained']} transformed={c['transformed']} "
            f"silent_drop={c['observed_silent_drop']} "
            f"passage_missing={c['passage_not_located']}"
        )
        machines.append(machine)

    # How to record judgments
    index_lines += [
        "",
        "## Recording item / coverage judgments",
        "",
        "```bash",
        "cd week-1",
        ".venv/bin/python -m evals.history.item_review record-item \\",
        "  --run extract-audit-replay-20260810T231331Z-6b58509e \\",
        "  --artifact art_extract_audit_replay_v2 \\",
        "  --chunk-sha <chunk_sha256> \\",
        "  --item-id '<item_id>' \\",
        "  --origin human --reviewer-id tj --reviewer-role engineer \\",
        "  --source-support pass --predicate fail --value uncertain \\",
        "  --metadata pass --deterministic-disposition pass \\",
        "  --notes '…' --refresh",
        "",
        ".venv/bin/python -m evals.history.item_review record-omission \\",
        "  --run extract-audit-replay-20260810T231331Z-6b58509e \\",
        "  --artifact art_extract_audit_replay_v2 \\",
        "  --chunk-sha <chunk_sha256> \\",
        "  --source-locator 'exact quote or locator' \\",
        "  --description 'omitted claim' \\",
        "  --origin human --reviewer-id tj --reviewer-role engineer \\",
        "  --proposed-predicate diagnosis --refresh",
        "```",
        "",
        "Or regenerate surfaces after hand-editing is never required:",
        "",
        "```bash",
        ".venv/bin/python -m evals.history.refresh_extraction_review_surfaces",
        "```",
        "",
    ]
    (_OUT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return machines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chunk",
        default=None,
        help="Single audit chunk JSON filename (default: render all via --all behavior)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Render every comparison page (default when --chunk omitted)",
    )
    parser.add_argument(
        "--with-reviews",
        action="store_true",
        help="Overlay append-only reviews from the corrected diagnostic run",
    )
    args = parser.parse_args(argv)

    if args.chunk and not args.all:
        path = _AUDIT / args.chunk
        ledger_facts = _load_ledger_facts()
        md, machine = render_chunk(path, ledger_facts=ledger_facts)
        stem = path.stem
        _OUT.mkdir(parents=True, exist_ok=True)
        (_OUT / f"{stem}.md").write_text(md, encoding="utf-8")
        (_OUT / f"{stem}.json").write_text(
            json.dumps(machine, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {_OUT.relative_to(_WEEK1)}/{stem}.md ({machine['counts']})")
        return 0

    store = None
    run_id = None
    artifact_id = None
    if args.with_reviews:
        from evals.history.item_review import DIAGNOSTIC_ARTIFACT_ID, DIAGNOSTIC_RUN_ID
        from evals.receipts.store import ReceiptStore

        store = ReceiptStore()
        run_id = DIAGNOSTIC_RUN_ID
        artifact_id = DIAGNOSTIC_ARTIFACT_ID

    machines = render_all_comparisons(
        store=store, run_id=run_id, artifact_id=artifact_id
    )
    print(f"wrote {len(machines)} comparison pages under {_OUT.relative_to(_WEEK1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
