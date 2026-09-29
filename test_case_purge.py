"""Delete-on-finish purge — local case dir + Langfuse session traces."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from case_purge import (
    LOCAL_CASES,
    local_case_dir,
    purge_case,
    safe_case_id,
)


class _FakeLangfuse:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def list_trace_ids(self, session_id: str) -> list[str]:
        assert session_id == "case-001"
        return ["tr_a", "tr_b"]

    def delete_trace(self, trace_id: str) -> None:
        self.deleted.append(trace_id)


def test_safe_case_id_rejects_path_traversal() -> None:
    with pytest.raises(ValueError):
        safe_case_id("../secret")
    with pytest.raises(ValueError):
        safe_case_id("a/b")
    with pytest.raises(ValueError):
        safe_case_id("")
    assert safe_case_id("case-001") == "case-001"


def test_purge_case_removes_local_dir_and_langfuse_traces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr("case_purge.LOCAL_CASES", tmp_path)
    case_dir = tmp_path / "case-001"
    case_dir.mkdir()
    (case_dir / "notes.txt").write_text("should vanish")
    fake = _FakeLangfuse()
    result = purge_case("case-001", langfuse_client=fake)
    assert result["case_id"] == "case-001"
    assert result["langfuse_traces_deleted"] == 2
    assert fake.deleted == ["tr_a", "tr_b"]
    assert not case_dir.exists()


def test_purge_endpoint_rejects_invalid_id() -> None:
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.post(
        "/case/purge",
        json={"confirm_synthetic": True, "case_id": "../etc"},
    )
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "invalid case_id"


def test_local_case_dir_stays_under_store() -> None:
    path = local_case_dir("fixture_001")
    assert path.parent == LOCAL_CASES
    assert path.name == "fixture_001"
