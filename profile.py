"""Runtime profile signal — fail-closed; one definition of restricted_allowed."""

from __future__ import annotations

import os
from typing import Literal

ProfileName = Literal["demo", "production"]
BackendName = Literal["openai", "bastion"]

_VALID_BACKENDS = frozenset({"openai", "bastion"})

_active_backend: BackendName = "openai"


def env_file_for_profile(profile: str | None) -> str:
    """Demo `.env` unless APP_PROFILE is exactly production."""
    return ".env.production" if profile == "production" else ".env"


def normalize_profile(raw: str | None) -> ProfileName:
    return "production" if raw == "production" else "demo"


def profile() -> ProfileName:
    return normalize_profile(os.getenv("APP_PROFILE"))


def backend_for_profile() -> BackendName:
    """Production always selects Bastion; demo stays OpenAI. No silent swap."""
    return "bastion" if profile() == "production" else "openai"


def set_active_backend(backend: str) -> BackendName:
    if backend not in _VALID_BACKENDS:
        raise ValueError(f"unsupported provider backend: {backend!r}")
    global _active_backend
    _active_backend = backend  # type: ignore[assignment]
    return _active_backend


def active_backend() -> BackendName:
    return _active_backend


def restricted_allowed() -> bool:
    return profile() == "production" and active_backend() == "bastion"


def posture() -> dict[str, object]:
    """Secret-free snapshot for /health and the operator console."""
    name = profile()
    backend = active_backend()
    allowed = restricted_allowed()
    backend_label = "Bastion" if backend == "bastion" else "OpenAI"
    return {
        "profile": name,
        "backend": backend,
        "restricted_allowed": allowed,
        "label": (
            f"{name.upper()} · {backend_label} · restricted {'ON' if allowed else 'OFF'}"
        ),
    }
