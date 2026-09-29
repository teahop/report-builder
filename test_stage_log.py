"""§4 stage logs carry outcomes and token counts, never request bodies."""

from __future__ import annotations

import json
import logging

from fastapi.testclient import TestClient

import main as main_mod
from schemas import IngestSuggestion
from stage_log import LOGGER


def test_ingest_success_logs_tokens_not_body(monkeypatch, caplog) -> None:
    def fake_classify(provider, *, content, model, today):
        return (
            IngestSuggestion(
                source_type="other",
                source_date="2026-01-01",
                label="test doc",
                doc_class="narrative",
            ),
            9,
            6,
            3,
        )

    monkeypatch.setattr(main_mod, "classify_document", fake_classify)
    caplog.set_level(logging.INFO, logger=LOGGER.name)
    client = TestClient(main_mod.app)
    secret = "Jordan Lee Quinn was retained in kindergarten"
    r = client.post(
        "/ingest",
        json={"confirm_synthetic": True, "content": secret},
    )
    assert r.status_code == 200, r.text
    records = [json.loads(rec.message) for rec in caplog.records if rec.name == LOGGER.name]
    assert records
    last = records[-1]
    assert last["stage"] == "ingest"
    assert last["outcome"] == "ok"
    assert last["tokens"] == 9
    assert last["profile"] == "demo"
    blob = " ".join(rec.message for rec in caplog.records)
    assert secret not in blob
    assert "Jordan" not in blob


def test_ingest_restricted_logs_refused_not_body(caplog) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER.name)
    client = TestClient(main_mod.app)
    secret = "restricted-case-body-should-not-log"
    r = client.post(
        "/ingest",
        json={"data_class": "restricted", "content": secret},
    )
    assert r.status_code == 403, r.text
    records = [json.loads(rec.message) for rec in caplog.records if rec.name == LOGGER.name]
    assert records
    last = records[-1]
    assert last["stage"] == "ingest"
    assert last["outcome"] == "refused"
    assert last["status_code"] == 403
    blob = " ".join(rec.message for rec in caplog.records)
    assert secret not in blob
    assert "restricted-case-body" not in r.json()["detail"]
