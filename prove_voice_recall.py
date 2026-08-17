"""Cross-session recall proof for Session 5 — human-readable stdout.

Write the store in one process (`python voice_store.py`), then score planted
drafts in a new process (`python voice_recall.py <draft.json>`). The recall
argv never contains rule text; the gate fires from voice_store.json on disk.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from voice_store import load_voice_store, voice_store_sha

_DIR = Path(__file__).resolve().parent
RECALL_DIR = _DIR / "evals" / "voice" / "recall"

# First slice A6 (Molly's paperwork opener), then A7 and A8.
SLICES: tuple[dict[str, str], ...] = (
    {
        "id": "A6",
        "rule_id": "voice.write_about_child",
        "draft": "a6_iep_documents.json",
        "needle": "The IEP documents indicate",
    },
    {
        "id": "A7",
        "rule_id": "voice.informants_distinct",
        "draft": "a7_blended_informants.json",
        "needle": "Reports from various sources",
    },
    {
        "id": "A8",
        "rule_id": "voice.no_meta_narration",
        "draft": "a8_meta_narration.json",
        "needle": "This narrative provides a snapshot",
    },
)


def _banner(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _rule_texts_must_not_be_input() -> list[str]:
    """Neutral ground-truth rule strings. Gate phrases are the draft, not this."""

    return [rec.rule for rec in load_voice_store() if rec.rule.strip()]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(_DIR),
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_no_rule_text_on_argv(args: list[str], rule_texts: list[str]) -> None:
    joined = " ".join(args)
    for text in rule_texts:
        if text in joined:
            raise AssertionError(
                f"recall process received rule text as input: {text!r}\n"
                f"argv: {args}"
            )


def main() -> int:
    _banner("WRITE PHASE — compile the store from DECISIONS.md (this process)")
    write_cmd = [sys.executable, str(_DIR / "voice_store.py")]
    print("$ " + " ".join(write_cmd))
    write = _run(write_cmd)
    sys.stdout.write(write.stdout)
    if write.returncode != 0:
        sys.stderr.write(write.stderr)
        print("WRITE PHASE FAILED")
        return write.returncode
    write_sha = voice_store_sha()
    print(f"write_sha={write_sha}")

    rule_texts = _rule_texts_must_not_be_input()
    recall_script = str(_DIR / "voice_recall.py")

    for slice_ in SLICES:
        draft_path = RECALL_DIR / slice_["draft"]
        _banner(
            f"RECALL PHASE — {slice_['id']} {slice_['rule_id']} "
            "(new process; rule text not on argv)"
        )
        recall_cmd = [sys.executable, recall_script, str(draft_path)]
        print("$ " + " ".join(recall_cmd))
        _assert_no_rule_text_on_argv(recall_cmd, rule_texts)
        # Draft JSON is temptation prose, not the rule statement.
        draft_payload = json.loads(draft_path.read_text(encoding="utf-8"))
        for text in rule_texts:
            blob = json.dumps(draft_payload)
            if text in blob:
                raise AssertionError(
                    f"draft {draft_path.name} contains rule text {text!r}"
                )
        recall = _run(recall_cmd)
        sys.stdout.write(recall.stdout)
        if recall.returncode != 0:
            sys.stderr.write(recall.stderr)
            print(f"RECALL PHASE FAILED for {slice_['id']}")
            return recall.returncode
        out = recall.stdout
        if f"FAIL {slice_['rule_id']}" not in out:
            raise AssertionError(
                f"{slice_['id']}: expected FAIL {slice_['rule_id']} in recall stdout:\n{out}"
            )
        if slice_["needle"] not in out:
            raise AssertionError(
                f"{slice_['id']}: expected span needle {slice_['needle']!r} in stdout:\n{out}"
            )
        if f"store_sha={write_sha}" not in out:
            raise AssertionError(
                f"{slice_['id']}: recall store_sha must match write_sha {write_sha}:\n{out}"
            )
        print(
            f"ASSERT ok: {slice_['id']} fired from disk store_sha={write_sha}; "
            "rule text was not argv input."
        )

    _banner("PROOF")
    print(
        "Gate fired in a process that never received the rule text. "
        "The record came from the store on disk."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
