"""Profile/backend signal — restricted_allowed is production ∧ bastion only."""

from __future__ import annotations

import pytest

import profile as profile_mod


@pytest.fixture(autouse=True)
def _reset_backend() -> None:
    profile_mod.set_active_backend("openai")
    yield
    profile_mod.set_active_backend("openai")


@pytest.mark.parametrize(
    "raw_profile,backend,want_profile,want_allowed",
    [
        (None, "openai", "demo", False),
        ("", "openai", "demo", False),
        ("garbage", "openai", "demo", False),
        ("demo", "openai", "demo", False),
        ("demo", "bastion", "demo", False),
        ("production", "openai", "production", False),
        ("production", "bastion", "production", True),
    ],
)
def test_restricted_allowed_truth_table(
    monkeypatch: pytest.MonkeyPatch,
    raw_profile: str | None,
    backend: str,
    want_profile: str,
    want_allowed: bool,
) -> None:
    if raw_profile is None:
        monkeypatch.delenv("APP_PROFILE", raising=False)
    else:
        monkeypatch.setenv("APP_PROFILE", raw_profile)
    profile_mod.set_active_backend(backend)
    assert profile_mod.profile() == want_profile
    assert profile_mod.active_backend() == backend
    assert profile_mod.restricted_allowed() is want_allowed


def test_unknown_backend_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported provider backend"):
        profile_mod.set_active_backend("anthropic")


@pytest.mark.parametrize(
    "raw_profile,want_backend",
    [
        (None, "openai"),
        ("demo", "openai"),
        ("garbage", "openai"),
        ("production", "bastion"),
    ],
)
def test_backend_for_profile(
    monkeypatch: pytest.MonkeyPatch,
    raw_profile: str | None,
    want_backend: str,
) -> None:
    if raw_profile is None:
        monkeypatch.delenv("APP_PROFILE", raising=False)
    else:
        monkeypatch.setenv("APP_PROFILE", raw_profile)
    assert profile_mod.backend_for_profile() == want_backend


def test_health_reports_demo_posture_without_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("APP_PROFILE", raising=False)
    from fastapi.testclient import TestClient

    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["profile"] == "demo"
    assert body["backend"] == "openai"
    assert body["restricted_allowed"] is False
    assert body["posture"] == "DEMO · OpenAI · restricted OFF"
    assert body["runtime"] == "openai-synthetic-only"
    blob = r.text.lower()
    for leaked in ("sk-", "pk-lf", "api_key", "bastiongpt_api_key"):
        assert leaked not in blob


def test_health_reports_production_bastion_posture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_PROFILE", "production")
    profile_mod.set_active_backend("bastion")
    from fastapi.testclient import TestClient

    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/health")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["profile"] == "production"
    assert body["backend"] == "bastion"
    assert body["restricted_allowed"] is True
    assert body["posture"] == "PRODUCTION · Bastion · restricted ON"
    assert body["runtime"] == "bastiongpt-api-v2.0"
    blob = r.text.lower()
    for leaked in ("sk-", "pk-lf", "api_key", "bastiongpt_api_key"):
        assert leaked not in blob
