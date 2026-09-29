"""Ingest and extract share the validation retry helper used by draft."""

from __future__ import annotations

from fastapi.testclient import TestClient

import main as main_mod
from schemas import IngestSuggestion


def test_ingest_retries_value_error_then_succeeds(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_classify(provider, *, content, model, today):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("malformed json")
        return (
            IngestSuggestion(
                source_type="other",
                source_date="2026-01-01",
                label="test doc",
                doc_class="narrative",
            ),
            3,
            2,
            1,
        )

    monkeypatch.setattr(main_mod, "classify_document", fake_classify)
    client = TestClient(main_mod.app)
    r = client.post(
        "/ingest",
        json={"confirm_synthetic": True, "content": "hello"},
    )
    assert r.status_code == 200, r.text
    assert calls["n"] == 2
    assert r.json()["suggestion"]["label"] == "test doc"


def test_ingest_exhausted_retries_return_502(monkeypatch) -> None:
    def always_bad(provider, *, content, model, today):
        raise ValueError("still malformed")

    monkeypatch.setattr(main_mod, "classify_document", always_bad)
    client = TestClient(main_mod.app)
    r = client.post(
        "/ingest",
        json={"confirm_synthetic": True, "content": "hello"},
    )
    assert r.status_code == 502, r.text
    assert "Ingest failed validation after retry" in r.json()["detail"]


def test_extract_retries_value_error_then_succeeds(monkeypatch) -> None:
    from schemas import Child, GapReport, Ledger

    calls = {"n": 0}
    child = Child(name="Test Child", dob="2015-01-01", evaluation_date="2026-01-01")
    empty = Ledger(
        child=child,
        ledger_version="1",
        built_at="2026-01-01T00:00:00Z",
        sources=[],
        facts=[],
    )

    def fake_build(provider, *, child, sources, model, prior_ledger=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("malformed json")
        return empty, {}, 0, 0, [], [], GapReport(), []

    monkeypatch.setattr(main_mod, "build_ledger", fake_build)
    client = TestClient(main_mod.app)
    r = client.post(
        "/extract",
        json={
            "confirm_synthetic": True,
            "skip_entailment": True,
            "child": {
                "name": "Test Child",
                "dob": "2015-01-01",
                "evaluation_date": "2026-01-01",
            },
            "sources": [
                {
                    "id": "doc_1",
                    "type": "other",
                    "date": "2026-01-01",
                    "label": "test",
                    "content": "hello",
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    assert calls["n"] == 2
