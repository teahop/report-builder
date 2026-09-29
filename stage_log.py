"""§4 process logs — stage outcomes and token counts, never bodies."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException

from profile import posture

LOGGER = logging.getLogger("report_builder.stage")

T = TypeVar("T")


def log_stage(
    *,
    stage: str,
    outcome: str,
    tokens: int | None = None,
    latency_ms: int | None = None,
    model: str | None = None,
    status_code: int | None = None,
) -> None:
    snap = posture()
    record: dict[str, Any] = {
        "stage": stage,
        "outcome": outcome,
        "profile": snap["profile"],
        "backend": snap["backend"],
    }
    if tokens is not None:
        record["tokens"] = tokens
    if latency_ms is not None:
        record["latency_ms"] = latency_ms
    if model is not None:
        record["model"] = model
    if status_code is not None:
        record["status_code"] = status_code
    LOGGER.info("%s", json.dumps(record, sort_keys=True))


def run_logged_stage(stage: str, operation: Callable[[], T]) -> T:
    try:
        result = operation()
    except HTTPException as exc:
        outcome = "refused" if exc.status_code == 403 else "error"
        log_stage(stage=stage, outcome=outcome, status_code=exc.status_code)
        raise
    log_stage(
        stage=stage,
        outcome="ok",
        tokens=getattr(result, "tokens_used", None),
        latency_ms=getattr(result, "latency_ms", None),
        model=getattr(result, "model", None),
    )
    return result
