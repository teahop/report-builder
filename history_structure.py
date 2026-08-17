"""Load and validate versioned History structure specs (Layer 2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent
STRUCTURES_DIR = _DIR / "history_structures"

KNOWN_SELECTORS = frozenset(
    {
        "family_history",
        "birth_developmental_history",
        "health_history",
        "social_history",
        "nurse_report",
        "educational_school_history",
        "educational_school_experience",
        "educational_intervention",
        "educational_iep",
        "covid_educational_experience",
        "previous_evaluations",
        "rater_input",
    }
)


class StructureSpecError(ValueError):
    """Invalid structure-spec file."""


def structure_spec_path(structure_spec_id: str) -> Path:
    return STRUCTURES_DIR / f"{structure_spec_id}.json"


def load_structure_spec(structure_spec_id: str) -> dict[str, Any]:
    path = structure_spec_path(structure_spec_id)
    if not path.is_file():
        raise StructureSpecError(f"Unknown structure_spec_id: {structure_spec_id!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_structure_spec(data)
    return data


def structure_spec_hash(structure_spec_id: str) -> str:
    raw = structure_spec_path(structure_spec_id).read_bytes()
    return hashlib.sha256(raw).hexdigest()


def validate_structure_spec(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise StructureSpecError("structure spec must be a JSON object")
    sid = data.get("structure_spec_id")
    if not isinstance(sid, str) or not sid.strip():
        raise StructureSpecError("structure_spec_id is required")
    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        raise StructureSpecError("sections must be a non-empty list")

    section_keys: set[str] = set()
    for section in sections:
        if not isinstance(section, dict):
            raise StructureSpecError("each section must be an object")
        sk = section.get("section_key")
        if not isinstance(sk, str) or not sk.strip():
            raise StructureSpecError("section_key is required")
        if sk in section_keys:
            raise StructureSpecError(f"duplicate section_key: {sk!r}")
        section_keys.add(sk)
        if not isinstance(section.get("display_label"), str):
            raise StructureSpecError(f"section {sk!r} needs display_label")
        if not isinstance(section.get("purpose"), str):
            raise StructureSpecError(f"section {sk!r} needs purpose")

        blocks = section.get("blocks")
        if not isinstance(blocks, list):
            raise StructureSpecError(f"section {sk!r} blocks must be a list")
        block_keys: set[str] = set()
        for block in blocks:
            if not isinstance(block, dict):
                raise StructureSpecError(f"section {sk!r} block must be an object")
            bk = block.get("block_key")
            if not isinstance(bk, str) or not bk.strip():
                raise StructureSpecError(f"section {sk!r} block_key is required")
            if bk in block_keys:
                raise StructureSpecError(
                    f"duplicate block_key {bk!r} in section {sk!r}"
                )
            block_keys.add(bk)
            selector = block.get("selector")
            if selector not in KNOWN_SELECTORS:
                raise StructureSpecError(
                    f"block {bk!r} references unknown selector {selector!r}"
                )
            if block.get("kind") not in {"prose", "table"}:
                raise StructureSpecError(f"block {bk!r} kind must be prose|table")
