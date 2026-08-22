"""Load a synthetic case fixture into the typed objects the pipeline expects.

These twelve lines lived in `test_all_stages.py`, which the migration classified
stay-behind — correctly, since the rest of that file is a homework smoke-runner.
But the classification was made from a dependency trace over `main.py`,
`demo_page.py`, and `prove_voice_recall.py` only; `evals/` was never traced, and
four eval scripts import from it. They arrived in this repo dead.

So the loader lives here, in the package that owns the fixtures it reads, and the
stay-behind ruling for everything else in that file still stands.
"""

from __future__ import annotations

import json
from pathlib import Path

from schemas import Child, Source

FIXTURES = Path(__file__).resolve().parent

FIXTURE_001_MANIFEST_PATH = FIXTURES / "fixture_001" / "manifest.json"

# Sibling evaluation fields — expectations the eval harness checks against.
# They travel with the fixture but must never reach a model prompt.
FIXTURE_META_KEYS = frozenset(
    {
        "expected_conflicts",
        "expected_facts",
        "expected_ledger_facts",
        "forbidden_predicates_by_source",
        "expected_gap_life_stages_empty",
        "expected_as_of_anchor",
        "expected_vague_no_anchor",
        "expected_grade_timeline",
    }
)


def load_case_manifest(manifest_path: Path) -> tuple[Child, list[Source], dict]:
    """Return (child, sources-in-arrival-order-with-doc_class, per_file_keys_by_id)."""

    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    child = Child.model_validate(man["child"])
    sources: list[Source] = []
    keys: dict = {}
    for f in man["files"]:
        fx = json.loads((manifest_path.parent / f["fixture"]).read_text(encoding="utf-8"))
        sources.append(Source.model_validate(fx["sources"][0]))
        keys[f["id"]] = {k: fx[k] for k in fx if k in FIXTURE_META_KEYS}
    return child, sources, keys


def strip_fixture_meta(fixture: dict, **overrides: object) -> dict:
    """Drop evaluation meta so it cannot reach a request or a model prompt."""

    payload = {k: v for k, v in fixture.items() if k not in FIXTURE_META_KEYS}
    payload.update(overrides)
    return payload
