"""Voice gate store — compiled from DECISIONS.md; review-only. No model calls."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from schemas import (
    Child,
    DraftBlock,
    DraftBlockKind,
    DraftProseOutput,
    DraftStatement,
    Fact,
    Ledger,
    Source,
)
from voice_store import (
    STORE_PATH,
    all_gate_strings,
    collect_prompt_texts,
    compiled_store_payload,
    decisions_ledger_status,
    evaluate_voice_gates,
    load_voice_store,
    review_items_from_gate,
    voice_store_sha,
    write_voice_store,
)

_DIR = Path(__file__).resolve().parent
RECALL_DIR = _DIR / "evals" / "voice" / "recall"


class LoudSkip(Exception):
    """Firewall could not inspect live prompts — not a pass."""


def _skip_loudly(reason: str) -> None:
    print(f"SKIP (loud): {reason}", file=sys.stderr)
    if os.environ.get("PYTEST_CURRENT_TEST"):
        import pytest

        pytest.skip(reason)
    raise LoudSkip(reason)


def _output(prose: str, *, label: str = "Family History") -> DraftProseOutput:
    return DraftProseOutput(
        blocks=[
            DraftBlock(
                kind=DraftBlockKind.PROSE,
                label=label,
                trigger=None,
                prose=prose,
                statements=[
                    DraftStatement(
                        statement="claim",
                        quote=prose[:40],
                        fact_ids=["f_fam_1"],
                    )
                ],
            )
        ],
        prose=f"**{label}:** {prose}",
        statements=[
            DraftStatement(statement="claim", quote=prose[:40], fact_ids=["f_fam_1"])
        ],
    )


def test_store_is_compiled_from_decisions_not_hand_edited() -> None:
    compiled = compiled_store_payload()
    on_disk = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    assert on_disk == compiled
    records = load_voice_store()
    ids = [r.id for r in records]
    assert ids == [
        "voice.labeled_blocks",
        "voice.complete_sentences",
        "voice.one_theme_per_block",
        "voice.supported_blocks",
        "voice.intervention_routing",
        "voice.write_about_child",
        "voice.informants_distinct",
        "voice.no_meta_narration",
    ]
    labeled = next(r for r in records if r.id == "voice.labeled_blocks")
    assert labeled.enforcement == "deterministic"
    assert labeled.cites == "schemas.DraftBlock"
    assert next(r for r in records if r.id == "voice.supported_blocks").ledger_required
    assert next(r for r in records if r.id == "voice.intervention_routing").ledger_required
    rewrite = write_voice_store()
    assert rewrite == STORE_PATH
    assert json.loads(STORE_PATH.read_text(encoding="utf-8")) == compiled


def test_a4_a5_not_applicable_without_ledger() -> None:
    output = _output("Jordan has a known peanut allergy.")
    report = evaluate_voice_gates(output, ledger=None, section_key=None)
    a4 = report.check_for("voice.supported_blocks")
    a5 = report.check_for("voice.intervention_routing")
    assert a4 is not None and a4.result == "not_applicable"
    assert a5 is not None and a5.result == "not_applicable"
    assert a4.result != "fail" and a5.result != "fail"


def test_a1_cites_draftblock_schema() -> None:
    labeled = _output("Jordan has a known peanut allergy.")
    report = evaluate_voice_gates(labeled)
    a1 = report.check_for("voice.labeled_blocks")
    assert a1 is not None and a1.result == "pass"
    unlabeled = DraftProseOutput(
        blocks=[],
        prose="Jordan has a known peanut allergy and walks to school every day.",
        statements=[],
    )
    failed = evaluate_voice_gates(unlabeled).check_for("voice.labeled_blocks")
    assert failed is not None and failed.result == "fail"


def test_a6_a7_a8_fire_on_planted_failures() -> None:
    a6 = evaluate_voice_gates(
        _output("Records indicate that Jordan has a documented peanut allergy.")
    ).check_for("voice.write_about_child")
    assert a6 is not None and a6.result == "fail"
    assert a6.span and "Records indicate" in a6.span

    a7 = evaluate_voice_gates(
        _output("Reports from various sources indicate that sleep is unsettled.")
    ).check_for("voice.informants_distinct")
    assert a7 is not None and a7.result == "fail"

    a8 = evaluate_voice_gates(
        _output(
            "Jordan enjoys drawing. This narrative provides a snapshot of her journey."
        )
    ).check_for("voice.no_meta_narration")
    assert a8 is not None and a8.result == "fail"
    items = review_items_from_gate(
        evaluate_voice_gates(
            _output("Records indicate that Jordan has a documented peanut allergy.")
        )
    )
    assert any(i.kind == "voice_gate" and i.voice_rule_id == "voice.write_about_child" for i in items)


def test_polarity_firewall_gate_strings_never_in_prompt() -> None:
    """A6/A7/A8 openers are review-only. They must not sit in generation text.

    If live prompts cannot be imported, skip loudly — never pass on an empty look.
    """

    toxic = {
        "records indicate",
        "the iep documents indicate",
        "reports from various sources indicate",
        "across various assessments",
        "this narrative provides a snapshot of her journey",
        "emphasizing the variability observed",
    }
    try:
        prompts = collect_prompt_texts()
    except (ImportError, OSError) as exc:
        _skip_loudly(
            "LIVE PROMPTS UNAVAILABLE — polarity firewall did not inspect "
            f"generation text: {exc}"
        )
    if not prompts:
        _skip_loudly(
            "LIVE PROMPTS UNAVAILABLE — polarity firewall had nothing to inspect"
        )
    for name, text in prompts.items():
        lowered = text.lower()
        for phrase in toxic:
            assert phrase not in lowered, f"{phrase!r} leaked into {name}"
    # Store still holds them for review.
    gates = " ".join(all_gate_strings()).lower()
    assert "records indicate" in gates


def test_decisions_ledger_status_missing_is_local_by_design() -> None:
    status = decisions_ledger_status(Path("/no/such/DECISIONS.md"))
    assert status["status"] == "local_by_design"
    assert status["status"] not in {"stale", "unknown"}
    assert "stays local by design" in status["message"]
    assert "compiled store is what ships" in status["message"]


def test_cross_session_recall_write_about_child() -> None:
    """Write the record, new process, A6 fires without the rule pasted in."""

    write_voice_store()
    sha = voice_store_sha()
    draft = RECALL_DIR / "a6_iep_documents.json"
    child = subprocess.run(
        [sys.executable, str(_DIR / "voice_recall.py"), str(draft)],
        cwd=str(_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert f"store_sha={sha}" in child.stdout
    assert "FAIL voice.write_about_child" in child.stdout
    assert "The IEP documents indicate" in child.stdout
    joined = " ".join(child.args)
    assert "Write about the child" not in joined
    assert "never the paperwork" not in joined


def test_cross_session_recall_a7_a8() -> None:
    write_voice_store()
    sha = voice_store_sha()
    slices = (
        ("a7_blended_informants.json", "voice.informants_distinct", "Reports from various sources"),
        ("a8_meta_narration.json", "voice.no_meta_narration", "This narrative provides a snapshot"),
    )
    for filename, rule_id, needle in slices:
        child = subprocess.run(
            [sys.executable, str(_DIR / "voice_recall.py"), str(RECALL_DIR / filename)],
            cwd=str(_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        assert child.returncode == 0, child.stderr
        assert f"store_sha={sha}" in child.stdout
        assert f"FAIL {rule_id}" in child.stdout
        assert needle in child.stdout
        joined = " ".join(child.args)
        assert "Informants stay distinct" not in joined
        assert "No meta-narration" not in joined


def test_prove_voice_recall_artifact() -> None:
    """The Session 5 proof script: write process, then recall process."""

    prove = subprocess.run(
        [sys.executable, str(_DIR / "prove_voice_recall.py")],
        cwd=str(_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert prove.returncode == 0, prove.stdout + "\n" + prove.stderr
    out = prove.stdout
    assert "phase=write" in out or "WRITE PHASE" in out
    assert "FAIL voice.write_about_child" in out
    assert "FAIL voice.informants_distinct" in out
    assert "FAIL voice.no_meta_narration" in out
    assert "The IEP documents indicate" in out
    assert "rule text was not argv input" in out


def test_no_module_loads_retired_draft_prompt() -> None:
    """Stage D prove: nothing loads draft_prompt.md; the HTTP route is gone."""

    week1 = Path(__file__).resolve().parent
    retired = week1 / "draft_prompt.md"
    assert not retired.exists()
    load_needles = (
        'draft_prompt.md").read_text',
        "draft_prompt.md').read_text",
        "DRAFT_SYSTEM_PROMPT =",
        "from draft import DRAFT_SYSTEM_PROMPT",
    )
    for path in week1.rglob("*.py"):
        if path.name == "test_voice_store.py":
            continue
        text = path.read_text(encoding="utf-8")
        for needle in load_needles:
            assert needle not in text, f"{path.name} still loads retired prompt via {needle!r}"
    import main as main_mod

    paths = set(main_mod.app.openapi().get("paths", {}))
    assert "/draft" not in paths
    assert "/draft/history" in paths
    assert "/draft/history/plan" in paths
    assert "/memory" in paths
    assert "/memory/store" in paths
    assert "/memory/recall" in paths


def test_a5_school_intervention_in_rater_section() -> None:
    ledger = Ledger(
        child=Child(name="Jordan Avery Quinn", dob="2014-05-01", evaluation_date="2025-06-01"),
        ledger_version="1",
        built_at="2025-06-01T00:00:00Z",
        sources=[
            Source(
                id="src_school",
                type="school",
                date="2025-03-01",
                label="School records",
                content="Tier 2 reading.",
            )
        ],
        facts=[
            Fact(
                id="f_tier_1",
                subject="child",
                predicate="intervention_tier",
                value="tier 2",
                value_text="tier 2 reading support",
                qualifier=None,
                assertion="asserted",
                source_id="src_school",
                source_date="2025-03-01",
                as_of_date="2025-03-01",
                reporter=None,
                life_stage="school-age",
                grade=None,
                temporality="as_of",
                confidence="stated",
            )
        ],
    )
    output = DraftProseOutput(
        blocks=[
            DraftBlock(
                kind=DraftBlockKind.PROSE,
                label="Caregiver Input",
                trigger=None,
                prose="Mother described tier 2 reading support at school.",
                statements=[
                    DraftStatement(
                        statement="Tier 2 reading.",
                        quote="tier 2 reading support",
                        fact_ids=["f_tier_1"],
                    )
                ],
            )
        ],
        prose="**Caregiver Input:** Mother described tier 2 reading support at school.",
        statements=[
            DraftStatement(
                statement="Tier 2 reading.",
                quote="tier 2 reading support",
                fact_ids=["f_tier_1"],
            )
        ],
    )
    fail = evaluate_voice_gates(
        output, ledger=ledger, section_key="rater_input"
    ).check_for("voice.intervention_routing")
    assert fail is not None and fail.result == "fail"
    ok = evaluate_voice_gates(
        output, ledger=ledger, section_key="educational_history"
    ).check_for("voice.intervention_routing")
    assert ok is not None and ok.result == "pass"


if __name__ == "__main__":
    tests = [
        test_store_is_compiled_from_decisions_not_hand_edited,
        test_a4_a5_not_applicable_without_ledger,
        test_a1_cites_draftblock_schema,
        test_a6_a7_a8_fire_on_planted_failures,
        test_polarity_firewall_gate_strings_never_in_prompt,
        test_decisions_ledger_status_missing_is_local_by_design,
        test_cross_session_recall_write_about_child,
        test_cross_session_recall_a7_a8,
        test_prove_voice_recall_artifact,
        test_a5_school_intervention_in_rater_section,
        test_no_module_loads_retired_draft_prompt,
    ]
    failed = 0
    skipped = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except LoudSkip as exc:
            skipped += 1
            print(f"SKIP {fn.__name__}: {exc}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    if skipped:
        print(f"{skipped} test(s) skipped loudly — not a pass.")
    raise SystemExit(1 if failed else 0)
