"""WP2b: deprecated stay-behind files stay gone; derived.py is live."""

from __future__ import annotations

from pathlib import Path

_DIR = Path(__file__).resolve().parent

_DEPRECATED_ABSENT = (
    "summary_prompt.md",
    "system_prompt.md",
    "grouping.py",
    "draft_prompt.md",
)


def test_manifest_deprecated_files_are_absent() -> None:
    for name in _DEPRECATED_ABSENT:
        assert not (_DIR / name).exists(), f"{name} should not be in this repo"


def test_derived_is_live_at_ledger_build() -> None:
    import derived
    import extract

    assert extract.inject_derived_and_request_facts is derived.inject_derived_and_request_facts
    doc = Path(derived.__file__).read_text(encoding="utf-8")
    assert "Live. Not deprecated" in doc
    assert derived.COMPUTED_AGE_FACT_ID == "f_computed_age_years"


def test_legacy_draft_absent_and_purge_registered() -> None:
    import main as main_mod

    paths = set(main_mod.app.openapi().get("paths", {}))
    assert "/draft" not in paths
    assert "/ask" in paths
    assert "/case/purge" in paths
