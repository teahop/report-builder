"""Refresh rebuildable extraction review surfaces without mutating receipts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_WEEK1 = Path(__file__).resolve().parents[2]
if str(_WEEK1) not in sys.path:
    sys.path.insert(0, str(_WEEK1))

from evals.history.item_review import (  # noqa: E402
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_RUN_ID,
    invalidated_sha_set,
    load_coverage_reviews,
    load_item_reviews,
    summarize_reviews,
)
from evals.history.render_item_comparison import (  # noqa: E402
    COMPARISON_PAGES,
    DEFAULT_CHUNK_STEM,
    render_all_comparisons,
)
from evals.receipts.review import (  # noqa: E402
    rebuild_current_review_view,
    rebuild_review_index,
)
from evals.receipts.store import ReceiptStore  # noqa: E402

_AUDIT = _WEEK1 / "evals" / "history" / "extraction_audit"
_OUT = _AUDIT / "item_comparison"


def rel_from_current_view(filename: str) -> str:
    """Path from runs/<id>/review_views/current/ to item_comparison/<file>."""

    return f"../../../../../../history/extraction_audit/item_comparison/{filename}"


def rel_from_run_index(filename: str) -> str:
    """Path from runs/<id>/index.md to item_comparison/<file>."""

    return f"../../../../history/extraction_audit/item_comparison/{filename}"


def comparison_nav_markdown(*, from_current_view: bool) -> str:
    rel = rel_from_current_view if from_current_view else rel_from_run_index
    lines = [
        "## Human-readable item comparisons",
        "",
        "_Navigation only — rebuildable. Does not change receipt or evidence hashes._",
        "",
        "- **Origin:** `targeted_chunk_replay` (temperature-0 re-extract of selected chunks).",
        "- **Not** the original 2026-08-10 Langfuse generations.",
        "- **Not** the parent of the legacy 77-fact cache (`legacy_untraceable`).",
        "- **Extraction content remains unreviewed** at the artifact level until a "
        "human records an artifact decision.",
        "",
        f"- [Item comparison README]({rel('README.md')})",
        f"- **Start here:** [`{DEFAULT_CHUNK_STEM}.md`]({rel(f'{DEFAULT_CHUNK_STEM}.md')})"
        " — seven-item review slice",
    ]
    for stem in COMPARISON_PAGES:
        lines.append(f"- [`{stem}.md`]({rel(f'{stem}.md')})")
    lines += [
        f"- [Extraction review summary]({rel('extraction_review_summary.md')})",
        "",
    ]
    return "\n".join(lines)


def write_extraction_summary(
    store: ReceiptStore,
    *,
    run_id: str,
    artifact_id: str,
    comparison_machines: list[dict],
) -> Path:
    receipt = store.load_receipt(run_id, artifact_id)
    item_records = load_item_reviews(store, run_id)
    coverage_records = load_coverage_reviews(store, run_id)

    raw_ids: list[str] = []
    silent_ids: list[str] = []
    retained_ids: list[str] = []
    chunk_hashes: dict[str, str] = {}
    for machine in comparison_machines:
        stem = Path(machine["artifact_file"]).stem
        chunk_hashes[stem] = machine["chunk_sha256"]
        for item in machine["items"]:
            iid = item["item_id"]
            raw_ids.append(iid)
            kind = item["disposition"]["kind"]
            if kind == "observed_silent_drop":
                silent_ids.append(iid)
            if kind in {"retained", "transformed"}:
                retained_ids.append(iid)

    summary = summarize_reviews(
        item_records=item_records,
        coverage_records=coverage_records,
        raw_item_ids=raw_ids,
        silent_drop_item_ids=silent_ids,
        retained_item_ids=retained_ids,
        artifact_id=artifact_id,
        artifact_sha256=receipt.artifact_sha256,
        chunk_hashes=chunk_hashes,
        invalidated_item_shas=invalidated_sha_set(
            store, run_id, kind="item_review"
        ),
        invalidated_coverage_shas=invalidated_sha_set(
            store, run_id, kind="coverage_review"
        ),
    )
    (_OUT / "extraction_review_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Extraction review summary",
        "",
        "_Rebuildable. Anchored to diagnostic artifact hashes. Not a pass rate._",
        "",
        f"- artifact: `{summary['artifact_id']}`",
        f"- artifact SHA-256: `{summary['artifact_sha256']}`",
        f"- run: `{run_id}`",
        f"- raw items: **{summary['raw_item_count']}**",
        f"- **human-reviewed items: {summary['human_reviewed_item_count']} of "
        f"{summary['raw_item_count']}**",
        f"- human-recorded omissions: **{summary['human_coverage_omission_count']}**",
        f"- human-unreviewed items: **{summary['human_unreviewed_item_count']}**",
        "",
        "### Not content-review progress",
        "",
        f"- invalidated test/demo item rows (preserved in log): "
        f"**{summary['invalidated_item_review_count']}**",
        f"- invalidated test/demo coverage rows: "
        f"**{summary['invalidated_coverage_omission_count']}**",
        f"- active synthetic item rows (should be 0 on the live run): "
        f"**{summary['synthetic_active_item_review_count']}**",
        f"- active synthetic coverage rows (should be 0 on the live run): "
        f"**{summary['synthetic_active_coverage_omission_count']}**",
        "",
        "## Chunk hashes",
        "",
    ]
    for stem, sha in sorted(summary["chunk_hashes"].items()):
        lines.append(f"- `{stem}`: `{sha}`")

    lines += [
        "",
        "## Counts by review dimension (latest **human** judgment per item)",
        "",
    ]
    lines.append("| Dimension | pass | fail | uncertain | not_applicable |")
    lines.append("|---|---:|---:|---:|---:|")
    for dim, counts in summary["human_dimension_counts"].items():
        lines.append(
            f"| `{dim}` | {counts['pass']} | {counts['fail']} | "
            f"{counts['uncertain']} | {counts['not_applicable']} |"
        )

    lines += ["", "## Observed silent drops", ""]
    if not summary["observed_silent_drop_item_ids"]:
        lines.append("_None._")
    else:
        for iid in summary["observed_silent_drop_item_ids"]:
            lines.append(f"- `{iid}`")

    lines += [
        "",
        "## Retained/transformed items with human fail/uncertain "
        "source_support, predicate, or value",
        "",
    ]
    problems = summary[
        "human_retained_with_failed_or_uncertain_support_predicate_or_value"
    ]
    if not problems:
        lines.append("_None recorded yet (or none human-reviewed as fail/uncertain)._")
    else:
        for p in problems:
            lines.append(
                f"- `{p['item_id']}` · chunk=`{p['chunk_sha256'][:12]}…` · "
                f"{p['dimensions']} · {p.get('reviewer_id')}/{p.get('origin')}"
                + (f" — {p['notes']}" if p.get("notes") else "")
            )

    lines += ["", "## Human-recorded omissions by chunk", ""]
    omissions = summary["human_coverage_omissions"]
    if not omissions:
        lines.append("_No human coverage omissions recorded yet._")
    else:
        by_chunk: dict[str, list] = {}
        for o in omissions:
            by_chunk.setdefault(o["chunk_sha256"], []).append(o)
        for chunk_sha, rows in sorted(by_chunk.items()):
            lines.append(f"### Chunk `{chunk_sha[:12]}…`")
            lines.append("")
            for o in rows:
                pred = o.get("proposed_predicate")
                pred_note = ""
                if pred:
                    flag = (
                        "provisional"
                        if o.get("proposed_predicate_provisional", True)
                        else "non-provisional"
                    )
                    pred_note = f" · proposed_predicate=`{pred}` ({flag})"
                span = ""
                if o.get("source_span_start") is not None:
                    span = (
                        f" · span=[{o['source_span_start']},"
                        f"{o.get('source_span_end')}]"
                    )
                lines.append(
                    f"- {o['description']} · locator={json.dumps(o['source_locator'])}"
                    f"{span}{pred_note} · {o['reviewer_id']}/{o['origin']}"
                )
            lines.append("")

    lines += [
        "",
        "## Human-unreviewed raw items",
        "",
    ]
    if not summary["human_unreviewed_item_ids"]:
        lines.append("_All raw items have at least one human judgment._")
    else:
        lines.append(
            f"_{summary['human_unreviewed_item_count']} items still without a "
            "human judgment (list truncated to 20):_"
        )
        lines.append("")
        for iid in summary["human_unreviewed_item_ids"][:20]:
            lines.append(f"- `{iid}`")
        if summary["human_unreviewed_item_count"] > 20:
            lines.append(
                f"- … +{summary['human_unreviewed_item_count'] - 20} more"
            )

    lines += [
        "",
        "## Log integrity",
        "",
        f"- item review log rows for this artifact SHA (including invalidated): "
        f"**{summary['item_review_log_count']}**",
        f"- coverage omission log rows (including invalidated): "
        f"**{summary['coverage_review_log_count']}**",
        "",
        "_Artifact acceptance remains a separate human decision after review._",
        "",
    ]
    path = _OUT / "extraction_review_summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _replace_or_append_section(text: str, marker: str, section: str) -> str:
    if marker in text:
        before, _, rest = text.partition(marker)
        # rest begins with content after marker title line may remain —
        # drop from after marker through next top-level ## section.
        # Find end of old section: first \n## that isn't the marker itself.
        cut = rest.find("\n## ")
        if cut >= 0:
            return before + section + rest[cut + 1 :]
        return before + section
    if "## Unresolved" in text:
        return text.replace("## Unresolved", section + "## Unresolved", 1)
    return text.rstrip() + "\n\n" + section


def inject_comparison_nav_into_current_view(
    store: ReceiptStore, run_id: str, artifact_id: str
) -> Path:
    """Rewrite rebuildable current view with comparison links; leave receipt alone."""

    path = rebuild_current_review_view(store, run_id, artifact_id)
    text = path.read_text(encoding="utf-8")
    nav = comparison_nav_markdown(from_current_view=True)
    text = _replace_or_append_section(text, "## Human-readable item comparisons", nav)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def inject_comparison_nav_into_index(store: ReceiptStore, run_id: str) -> Path:
    path = rebuild_review_index(store, run_id)
    text = path.read_text(encoding="utf-8")
    nav = comparison_nav_markdown(from_current_view=False)
    text = _replace_or_append_section(text, "## Human-readable item comparisons", nav)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def refresh_all(
    *,
    store: ReceiptStore | None = None,
    run_id: str = DIAGNOSTIC_RUN_ID,
    artifact_id: str = DIAGNOSTIC_ARTIFACT_ID,
) -> dict:
    store = store or ReceiptStore()
    machines = render_all_comparisons(
        store=store, run_id=run_id, artifact_id=artifact_id
    )
    summary_path = write_extraction_summary(
        store, run_id=run_id, artifact_id=artifact_id, comparison_machines=machines
    )
    current = inject_comparison_nav_into_current_view(store, run_id, artifact_id)
    index = inject_comparison_nav_into_index(store, run_id)
    # Also write a stable nav pointer beside the run for humans.
    nav_path = store.run_dir(run_id) / "extraction_comparisons.md"
    nav_path.write_text(
        "# Extraction comparison navigation\n\n"
        + comparison_nav_markdown(from_current_view=False),
        encoding="utf-8",
    )
    return {
        "summary": str(summary_path),
        "current_review": str(current),
        "index": str(index),
        "nav": str(nav_path),
        "chunks": len(machines),
    }


def main() -> None:
    print(json.dumps(refresh_all(), indent=2))


if __name__ == "__main__":
    main()
