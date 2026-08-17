"""Structure-matched History few-shot registry (Layer 4)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

EvidenceShape = Literal["ordinary", "sparse", "conflict_variance"]

_DIR = Path(__file__).resolve().parent
_REGISTRY_PATH = _DIR / "history_fewshots" / "registry.json"


@dataclass(frozen=True, slots=True)
class FewShotExample:
    example_id: str
    structure_spec_id: str
    section_key: str
    block_keys: tuple[str, ...]
    evidence_shape: EvidenceShape
    demonstrates: tuple[str, ...]
    input_brief: dict[str, Any]
    output: dict[str, Any]


def _load_raw() -> list[dict[str, Any]]:
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("few-shot registry must be a JSON list")
    return data


def load_fewshot_registry() -> list[FewShotExample]:
    out: list[FewShotExample] = []
    for row in _load_raw():
        out.append(
            FewShotExample(
                example_id=row["example_id"],
                structure_spec_id=row["structure_spec_id"],
                section_key=row["section_key"],
                block_keys=tuple(row["block_keys"]),
                evidence_shape=row["evidence_shape"],
                demonstrates=tuple(row.get("demonstrates") or []),
                input_brief=row["input_brief"],
                output=row["output"],
            )
        )
    return out


def select_fewshots(
    *,
    structure_spec_id: str,
    section_key: str,
    block_keys: list[str],
    evidence_shape: EvidenceShape = "ordinary",
    limit: int = 2,
) -> list[FewShotExample]:
    """
    Deterministic match: structure version + section required; block overlap
    and evidence_shape preferred. Never cross structure versions or sections.
    """

    block_set = set(block_keys)
    candidates: list[tuple[int, str, FewShotExample]] = []
    for ex in load_fewshot_registry():
        if ex.structure_spec_id != structure_spec_id:
            continue
        if ex.section_key != section_key:
            continue
        overlap = len(block_set.intersection(ex.block_keys))
        shape_bonus = 2 if ex.evidence_shape == evidence_shape else 0
        # Prefer examples whose block_keys are covered by the case (or dynamic
        # rater prefix match for caregiver_input:*).
        prefix_hits = 0
        for bk in ex.block_keys:
            if bk in block_set:
                continue
            if any(
                case_bk == bk or case_bk.startswith(bk.rstrip(":") + ":") or bk.endswith(":")
                and case_bk.startswith(bk)
                for case_bk in block_set
            ):
                prefix_hits += 1
            # Caregiver template: example tagged caregiver_input matches any caregiver_input:*
            if bk == "caregiver_input" and any(
                c.startswith("caregiver_input:") for c in block_set
            ):
                prefix_hits += 1
        score = overlap * 10 + prefix_hits * 5 + shape_bonus
        if score <= 0 and not block_set.intersection(ex.block_keys):
            # Still allow section-level ordinary examples when block tags are
            # templates (caregiver_input) or thematic parents.
            thematic = {
                "family_history",
                "birth_developmental_history",
                "health_history",
                "caregiver_input",
            }
            if not any(
                (b in thematic and (b in block_set or any(c.startswith(b) for c in block_set)))
                for b in ex.block_keys
            ):
                continue
            score = 1 + shape_bonus
        candidates.append((-score, ex.example_id, ex))

    candidates.sort()
    return [ex for _, _, ex in candidates[:limit]]


# --- Phase 1 approved-excerpt examples (positive voice channel) ---

PHASE1_REGISTRY_PATH = _DIR / "history_fewshots" / "phase1" / "registry.json"

_PHASE1_SECTION_EXAMPLE_ID = {
    "current_status_history": "phase1_A_current_status_case_003",
    "educational_history": "phase1_B_educational_history_case_005",
    "previous_evaluations": "phase1_C_previous_evaluations_case_006",
    "rater_input": "phase1_D_rater_input_case_004",
}


def load_phase1_registry() -> list[dict[str, Any]]:
    data = json.loads(PHASE1_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("phase1 registry must be a JSON list")
    return data


def select_phase1_example(section_key: str) -> dict[str, Any]:
    wanted = _PHASE1_SECTION_EXAMPLE_ID.get(section_key)
    if wanted is None:
        raise ValueError(f"no Phase 1 example mapped for section {section_key!r}")
    for row in load_phase1_registry():
        if row["example_id"] == wanted:
            blob = json.dumps(row).lower()
            if "fixture_001" in blob or "emma rose" in blob:
                raise RuntimeError("fixture_001/Emma leaked into a Phase 1 example")
            return row
    raise ValueError(f"Phase 1 example {wanted!r} missing from registry")


def format_phase1_user_message(example: dict[str, Any]) -> str:
    """Serialize the approved-excerpt user side as a real chat message."""

    user = example["example_user"]
    payload = {
        "section_label": user.get("section_label") or example.get("display_label"),
        "section_plan": user.get("section_plan") or [],
        "evidence": user.get("evidence") or {},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
