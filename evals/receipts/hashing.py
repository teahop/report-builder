"""Canonical hashing and content-addressed artifact writes (eval-only)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic JSON encoding for hashing — sorted keys, compact separators."""

    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_canonical(obj: Any) -> str:
    return sha256_bytes(canonical_json_bytes(obj))


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


class ContentAddressConflict(RuntimeError):
    """Raised when writing different bytes to an existing content-addressed path."""


def write_content_addressed(
    store_dir: Path,
    obj: Any,
    *,
    suffix: str = ".json",
) -> tuple[str, Path]:
    """
    Write ``obj`` under ``store_dir/<sha256><suffix>``.

    Allowed to rewrite only when bytes are identical; otherwise fail loudly.
    """

    store_dir.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(obj)
    digest = sha256_bytes(payload)
    path = store_dir / f"{digest}{suffix}"
    if path.exists():
        existing = path.read_bytes()
        if existing != payload:
            raise ContentAddressConflict(
                f"content-addressed path {path.name} already holds different bytes"
            )
        return digest, path
    path.write_bytes(payload)
    return digest, path


def write_content_addressed_text(
    store_dir: Path,
    text: str,
    *,
    suffix: str = ".md",
) -> tuple[str, Path]:
    store_dir.mkdir(parents=True, exist_ok=True)
    payload = text.encode("utf-8")
    digest = sha256_bytes(payload)
    path = store_dir / f"{digest}{suffix}"
    if path.exists():
        if path.read_bytes() != payload:
            raise ContentAddressConflict(
                f"content-addressed path {path.name} already holds different bytes"
            )
        return digest, path
    path.write_bytes(payload)
    return digest, path
