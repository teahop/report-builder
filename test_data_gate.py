"""Restricted-data gate — one predicate, fail closed, no submitted content in refusals."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

import profile as profile_mod
from data_gate import assert_data_permitted, refusal_detail, resolve_data_class


@pytest.fixture(autouse=True)
def _reset_backend() -> None:
    profile_mod.set_active_backend("openai")
    yield
    profile_mod.set_active_backend("openai")


@pytest.mark.parametrize(
    "data_class,confirm_synthetic,want",
    [
        ("synthetic", None, "synthetic"),
        ("restricted", None, "restricted"),
        (None, True, "synthetic"),
        (None, False, "restricted"),
        (None, None, "restricted"),
        ("nope", True, "restricted"),
        ("nope", None, "restricted"),
    ],
)
def test_resolve_data_class(
    data_class: str | None,
    confirm_synthetic: bool | None,
    want: str,
) -> None:
    assert resolve_data_class(data_class, confirm_synthetic) == want


@pytest.mark.parametrize(
    "raw_profile,backend,data_class,confirm_synthetic,allowed",
    [
        ("demo", "openai", "synthetic", None, True),
        ("demo", "openai", None, True, True),
        ("production", "bastion", "synthetic", None, True),
        ("production", "bastion", "restricted", None, True),
        ("demo", "openai", "restricted", None, False),
        ("demo", "bastion", "restricted", None, False),
        ("production", "openai", "restricted", None, False),
        ("demo", "openai", None, None, False),
        ("production", "openai", None, False, False),
    ],
)
def test_assert_data_permitted_truth_table(
    monkeypatch: pytest.MonkeyPatch,
    raw_profile: str,
    backend: str,
    data_class: str | None,
    confirm_synthetic: bool | None,
    allowed: bool,
) -> None:
    monkeypatch.setenv("APP_PROFILE", raw_profile)
    profile_mod.set_active_backend(backend)
    if allowed:
        assert_data_permitted(
            data_class=data_class,
            confirm_synthetic=confirm_synthetic,
        )
        return
    with pytest.raises(HTTPException) as exc:
        assert_data_permitted(
            data_class=data_class,
            confirm_synthetic=confirm_synthetic,
        )
    assert exc.value.status_code == 403
    detail = exc.value.detail
    assert isinstance(detail, str)
    assert detail.startswith("Restricted data refused:")
    assert "emma" not in detail.lower()
    assert "Callahan" not in detail


def test_refusal_names_failing_condition_not_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_PROFILE", "demo")
    profile_mod.set_active_backend("openai")
    detail = refusal_detail()
    assert "profile is not production" in detail
    assert "backend is not Bastion" in detail


def test_ingest_refuses_restricted_on_demo_before_model() -> None:
    from fastapi.testclient import TestClient

    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.post(
        "/ingest",
        json={"data_class": "restricted", "content": "secret case text"},
    )
    assert r.status_code == 403, r.text
    detail = r.json()["detail"]
    assert "Restricted data refused" in detail
    assert "secret case text" not in detail
    assert "secret" not in detail
