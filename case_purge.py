"""Delete-on-finish: local case artifacts + Langfuse traces for one case_id."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field

from data_gate import DataClassification

_CASE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
LOCAL_CASES = Path(__file__).resolve().parent / "local_store" / "cases"


class LangfuseTraceClient(Protocol):
    def list_trace_ids(self, session_id: str) -> list[str]: ...
    def delete_trace(self, trace_id: str) -> None: ...


class CasePurgeRequest(DataClassification):
    case_id: str = Field(min_length=1, max_length=128)


class CasePurgeResponse(BaseModel):
    case_id: str
    local_deleted: list[str]
    langfuse_traces_deleted: int


def safe_case_id(case_id: str) -> str:
    if not case_id or not _CASE_ID_RE.fullmatch(case_id):
        raise ValueError("invalid case_id")
    return case_id


def local_case_dir(case_id: str) -> Path:
    return LOCAL_CASES / safe_case_id(case_id)


def purge_local_case(case_id: str) -> list[str]:
    path = local_case_dir(case_id)
    if not path.is_dir():
        return []
    shutil.rmtree(path)
    return [str(path)]


class EnvLangfuseTraceClient:
    """Public Langfuse REST — traces for a session, then delete each."""

    def __init__(self) -> None:
        self.host = (
            os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or ""
        ).rstrip("/")
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY") or ""
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY") or ""

    def _enabled(self) -> bool:
        return bool(self.host and self.public_key and self.secret_key)

    def list_trace_ids(self, session_id: str) -> list[str]:
        if not self._enabled():
            return []
        response = httpx.get(
            f"{self.host}/api/public/traces",
            params={"sessionId": session_id, "limit": 100},
            auth=(self.public_key, self.secret_key),
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("data") or payload.get("traces") or []
        ids: list[str] = []
        for row in rows:
            if isinstance(row, dict) and row.get("id"):
                ids.append(str(row["id"]))
        return ids

    def delete_trace(self, trace_id: str) -> None:
        if not self._enabled():
            return
        response = httpx.delete(
            f"{self.host}/api/public/traces/{trace_id}",
            auth=(self.public_key, self.secret_key),
            timeout=30.0,
        )
        response.raise_for_status()


def delete_langfuse_session(
    session_id: str,
    *,
    client: LangfuseTraceClient | None = None,
) -> int:
    cid = safe_case_id(session_id)
    api = client or EnvLangfuseTraceClient()
    ids = api.list_trace_ids(cid)
    for trace_id in ids:
        api.delete_trace(trace_id)
    return len(ids)


def purge_case(
    case_id: str,
    *,
    langfuse_client: LangfuseTraceClient | None = None,
) -> dict[str, Any]:
    cid = safe_case_id(case_id)
    local = purge_local_case(cid)
    traces = delete_langfuse_session(cid, client=langfuse_client)
    return {
        "case_id": cid,
        "local_deleted": local,
        "langfuse_traces_deleted": traces,
    }
