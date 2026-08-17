"""Generate immutable evidence views and rebuildable current review views."""

from __future__ import annotations

from collections import Counter
from typing import Any

from evals.receipts.models import StageEvalRecord, StageReceipt
from evals.receipts.review import latest_decision_for, load_decisions, review_status
from evals.receipts.store import ReceiptStore


def _disposition_label(kind: str) -> str:
    if kind == "observed_silent_drop":
        return "observed silent drop"
    return kind


def render_evidence_markdown(
    receipt: StageReceipt,
    *,
    decisions_payload: dict[str, Any] | None = None,
) -> str:
    """
    Immutable evidence view — derived from receipt/stage evidence only.

    Must never include mutable review status or append-only eval results.
    """

    lines: list[str] = [
        f"# Evidence view — `{receipt.artifact_id}`",
        "",
        "_Immutable evidence. Review status and eval results live in the "
        "rebuildable current review view — not here._",
        "",
        f"- run: `{receipt.run_id}`",
        f"- stage: `{receipt.stage}`",
        f"- lineage: `{receipt.lineage}`",
        f"- receipt_version: `{receipt.receipt_version}`",
        f"- artifact SHA-256: `{receipt.artifact_sha256}`",
        f"- created_at: `{receipt.created_at}` _(metadata; not in artifact hash)_",
    ]

    lines += ["", "## Parents", ""]
    if not receipt.parents:
        lines.append("_No parents._")
    else:
        for p in receipt.parents:
            lines.append(
                f"- `{p.artifact_id}` stage=`{p.stage}` sha=`{p.sha256[:12]}…` "
                f"required_accepted={p.required_accepted}"
            )

    lines += ["", "## Configuration", ""]
    cfg = receipt.config
    lines.append(f"- git_sha: `{cfg.git_sha}`")
    lines.append(f"- code_fingerprint: `{cfg.code_fingerprint}`")
    lines.append(f"- prompt_sha256: `{cfg.prompt_sha256}`")
    lines.append(f"- structure_spec_id: `{cfg.structure_spec_id}`")
    lines.append(f"- structure_spec_sha256: `{cfg.structure_spec_sha256}`")
    lines.append(f"- model: `{cfg.model}` temperature=`{cfg.temperature}`")
    if cfg.extra:
        for k, v in sorted(cfg.extra.items()):
            lines.append(f"- extra.{k}: `{v}`")

    lines += ["", "## Counts", ""]
    if receipt.counts:
        for k, v in sorted(receipt.counts.items()):
            lines.append(f"- {k}: **{v}**")
    else:
        lines.append("_No counts._")

    if receipt.tokens:
        lines += ["", "## Tokens / cost", ""]
        for k, v in sorted(receipt.tokens.items()):
            lines.append(f"- {k}: `{v}`")

    lines += ["", "## Dispositions", ""]
    decisions = decisions_payload
    if decisions is None and receipt.deterministic_decisions is not None:
        # Caller should pass payload when hashing evidence before store read;
        # when rendering from an existing receipt, load from store in current view.
        lines.append(
            "_Pass decisions_payload when building; see current review view "
            "if this evidence view was stored without inline dispositions._"
        )
    elif not decisions:
        lines.append("_No deterministic-decisions artifact attached._")
    else:
        _append_disposition_sections(lines, decisions, include_acceptance_blocker=True)

    lines += ["", "## Machine artifact paths", ""]
    lines.append(
        f"- machine_output: `{receipt.machine_output.relative_path}` "
        f"(sha `{receipt.machine_output.sha256[:12]}…`)"
    )
    if receipt.deterministic_decisions:
        lines.append(
            f"- deterministic_decisions: `{receipt.deterministic_decisions.relative_path}` "
            f"(sha `{receipt.deterministic_decisions.sha256[:12]}…`)"
        )
    lines.append(
        f"- receipt: `runs/{receipt.run_id}/receipts/{receipt.artifact_id}.json`"
    )

    if receipt.notes:
        lines += ["", "## Notes", "", receipt.notes]

    # Guard: never emit review status words that imply current decision state.
    text = "\n".join(lines).rstrip() + "\n"
    return text


def _append_disposition_sections(
    lines: list[str],
    decisions: dict[str, Any],
    *,
    include_acceptance_blocker: bool,
) -> None:
    disp = decisions.get("dispositions") or decisions.get("brief_dispositions") or []
    kind_counts = Counter(
        (d.get("kind") if isinstance(d, dict) else getattr(d, "kind", "?"))
        for d in disp
    )
    lines.append("### By kind")
    lines.append("")
    for k, n in sorted(kind_counts.items()):
        lines.append(f"- `{_disposition_label(k)}`: {n}")
    lines.append("")
    lines.append("### Notable items")
    lines.append("")
    notable_kinds = {
        "transformed",
        "quarantined",
        "suppressed_duplicate",
        "not_draftable",
        "error",
        "held_for_review",
        "routed_elsewhere",
        "observed_silent_drop",
    }
    shown = 0
    for d in disp:
        kind = d.get("kind") if isinstance(d, dict) else d.kind
        if kind not in notable_kinds:
            continue
        item = d.get("item_id") or d.get("fact_id")
        reason = d.get("reason") or d.get("error") or ""
        gate = d.get("gate_or_check") or ""
        label = _disposition_label(kind)
        extra = f" · gate=`{gate}`" if gate else ""
        lines.append(f"- **{label}** · `{item}` · {reason}{extra}")
        shown += 1
    if shown == 0:
        lines.append("_No transformed/quarantined/duplicate/error/silent-drop items._")

    review_items = decisions.get("quarantine_review_items") or []
    if review_items:
        lines += ["", "### Quarantine review items", ""]
        for qi in review_items:
            lines.append(
                f"- `{qi.get('review_item_id')}` ← `{qi.get('item_id')}`: "
                f"{qi.get('reason')}"
            )

    if include_acceptance_blocker and kind_counts.get("observed_silent_drop"):
        lines += [
            "",
            "### Acceptance blocker",
            "",
            "- This artifact contains **observed silent drop** items.",
            "- It cannot become an accepted evaluable parent until a new run "
            "gives every item a valid evaluable disposition "
            "(quarantine / not_draftable / retained / …).",
        ]


def render_current_review_markdown(
    store: ReceiptStore,
    receipt: StageReceipt,
    *,
    decisions_payload: dict[str, Any] | None = None,
    eval_records: list[StageEvalRecord] | None = None,
) -> str:
    """Rebuildable current review surface — receipt + decisions + evals."""

    from evals.receipts.stage_evals import load_eval_records_for_artifact

    status = review_status(store, receipt.run_id, receipt.artifact_id)
    latest = latest_decision_for(
        load_decisions(store, receipt.run_id), receipt.artifact_id
    )
    if eval_records is None:
        eval_records = load_eval_records_for_artifact(
            store, receipt.run_id, receipt.artifact_id
        )

    decisions = decisions_payload
    if decisions is None and receipt.deterministic_decisions is not None:
        decisions = store.read_artifact_json(receipt.deterministic_decisions)

    lines: list[str] = [
        f"# Current review — `{receipt.artifact_id}`",
        "",
        "_Rebuildable view. Sources of truth: receipt, decisions.jsonl, evals.jsonl._",
        "",
        f"- run: `{receipt.run_id}`",
        f"- stage: `{receipt.stage}`",
        f"- lineage: `{receipt.lineage}`",
        f"- artifact SHA-256: `{receipt.artifact_sha256}`",
        f"- created_at: `{receipt.created_at}` _(metadata; not in artifact hash)_",
        f"- review status: **{status}**",
    ]
    if latest:
        origin = getattr(latest, "origin", None) or "unknown_v1"
        lines.append(
            f"- latest decision: `{latest.decision}` · origin=`{origin}` · "
            f"reviewer=`{latest.reviewer_id}` / `{latest.reviewer_role}` · "
            f"at {latest.reviewed_at}"
        )
        if origin == "synthetic_test":
            lines.append(
                "- **Not human approval** — this is a synthetic_test / harness decision."
            )
        if latest.notes:
            lines.append(f"- decision notes: {latest.notes}")
    else:
        lines.append("- latest decision: _unreviewed_")

    if receipt.evidence_view:
        lines.append(
            f"- immutable evidence view: `{receipt.evidence_view.relative_path}` "
            f"(sha `{receipt.evidence_view.sha256[:12]}…`)"
        )

    lines += ["", "## Parents", ""]
    if not receipt.parents:
        lines.append("_No parents._")
    else:
        for p in receipt.parents:
            lines.append(
                f"- `{p.artifact_id}` stage=`{p.stage}` sha=`{p.sha256[:12]}…` "
                f"required_accepted={p.required_accepted}"
            )

    lines += ["", "## Configuration", ""]
    cfg = receipt.config
    lines.append(f"- git_sha: `{cfg.git_sha}`")
    lines.append(f"- code_fingerprint: `{cfg.code_fingerprint}`")
    lines.append(f"- prompt_sha256: `{cfg.prompt_sha256}`")
    lines.append(f"- structure_spec_id: `{cfg.structure_spec_id}`")
    lines.append(f"- structure_spec_sha256: `{cfg.structure_spec_sha256}`")
    lines.append(f"- model: `{cfg.model}` temperature=`{cfg.temperature}`")

    lines += ["", "## Counts", ""]
    if receipt.counts:
        for k, v in sorted(receipt.counts.items()):
            lines.append(f"- {k}: **{v}**")
    else:
        lines.append("_No counts._")

    lines += ["", "## Dispositions", ""]
    if not decisions:
        lines.append("_No deterministic-decisions artifact attached._")
    else:
        _append_disposition_sections(lines, decisions, include_acceptance_blocker=True)

    lines += ["", "## Append-only eval results", ""]
    if not eval_records:
        # v1 receipts may still carry embedded eval_results — show as legacy only.
        if receipt.eval_results:
            lines.append(
                "_Legacy v1 embedded eval_results (prefer evals.jsonl for new work):_"
            )
            for ev in receipt.eval_results:
                lines.append(
                    f"- `{ev.check_id}`@{ev.check_version}: **{ev.result}** "
                    f"(items={ev.evidence_item_ids})"
                    + (f" — {ev.detail}" if ev.detail else "")
                )
        else:
            lines.append("_No eval records yet._")
    else:
        lines.append(
            "_All recorded versions are listed; nothing is silently collapsed._"
        )
        lines.append("")
        for ev in eval_records:
            origin = ev.evaluator_origin or "—"
            eid = ev.evaluator_id or "—"
            lines.append(
                f"- `{ev.check_id}`@{ev.check_version}: **{ev.result}** · "
                f"sha=`{ev.artifact_sha256[:12]}…` · recorded `{ev.recorded_at}` · "
                f"evaluator=`{eid}` origin=`{origin}`"
                + (f" — {ev.detail}" if ev.detail else "")
            )
            if ev.evidence_item_ids:
                lines.append(f"  - evidence items: `{ev.evidence_item_ids}`")

    lines += ["", "## Machine artifact paths", ""]
    lines.append(
        f"- machine_output: `{receipt.machine_output.relative_path}` "
        f"(sha `{receipt.machine_output.sha256[:12]}…`)"
    )
    if receipt.deterministic_decisions:
        lines.append(
            f"- deterministic_decisions: `{receipt.deterministic_decisions.relative_path}` "
            f"(sha `{receipt.deterministic_decisions.sha256[:12]}…`)"
        )
    if receipt.evidence_view:
        lines.append(
            f"- evidence_view: `{receipt.evidence_view.relative_path}` "
            f"(sha `{receipt.evidence_view.sha256[:12]}…`)"
        )
    lines.append(
        f"- receipt: `runs/{receipt.run_id}/receipts/{receipt.artifact_id}.json`"
    )
    lines.append(
        f"- current review (this file): "
        f"`runs/{receipt.run_id}/review_views/current/{receipt.artifact_id}.md`"
    )

    if receipt.notes:
        lines += ["", "## Notes", "", receipt.notes]

    if status == "unreviewed":
        lines += [
            "",
            "## Unresolved",
            "",
            "- This artifact has **no** append-only review decision yet.",
            "- It cannot be an evaluable downstream parent until `accepted` "
            "with a truthful decision origin.",
        ]
    elif status == "accepted" and latest and getattr(latest, "origin", None) == "synthetic_test":
        lines += [
            "",
            "## Note on acceptance",
            "",
            "- Accepted only under `synthetic_test` origin for gate mechanics.",
            "- Does **not** claim human review of a real/approved-anonymized case.",
        ]

    return "\n".join(lines).rstrip() + "\n"


# Back-compat alias used by older call sites during migration.
def render_review_markdown(
    store: ReceiptStore,
    receipt: StageReceipt,
    *,
    decisions_payload: dict[str, Any] | None = None,
) -> str:
    return render_current_review_markdown(
        store, receipt, decisions_payload=decisions_payload
    )
