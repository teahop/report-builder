"""Env-file selector for APP_PROFILE — demo by default, production only when named."""

from __future__ import annotations

from main import env_file_for_profile


def test_production_profile_loads_production_env() -> None:
    assert env_file_for_profile("production") == ".env.production"


def test_demo_profile_loads_demo_env() -> None:
    assert env_file_for_profile("demo") == ".env"


def test_unset_profile_fails_closed_to_demo_env() -> None:
    assert env_file_for_profile(None) == ".env"


def test_unknown_profile_fails_closed_to_demo_env() -> None:
    assert env_file_for_profile("garbage") == ".env"
