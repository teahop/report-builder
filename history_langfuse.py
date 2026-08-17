"""Langfuse helpers for the History package path.

Keys come from env (LANGFUSE_PUBLIC_KEY / SECRET_KEY + HOST or BASE_URL).
Missing keys → no-op; drafting still works.
"""

from __future__ import annotations

from typing import Any

from history_schemas import HistoryDraftResponse


def attach_langfuse_ids(response: HistoryDraftResponse) -> HistoryDraftResponse:
    """Copy current trace id/URL onto the response when a trace is active."""

    try:
        from langfuse import get_client

        lf = get_client()
        trace_id = lf.get_current_trace_id()
        url = lf.get_trace_url(trace_id=trace_id) if trace_id else None
        response.trace_id = trace_id
        response.langfuse_url = url
    except Exception:
        response.trace_id = None
        response.langfuse_url = None
    return response


def update_history_trace_metadata(**metadata: Any) -> None:
    """Best-effort metadata on the current observe span."""

    try:
        from langfuse import get_client

        get_client().update_current_span(metadata={k: v for k, v in metadata.items() if v is not None})
    except Exception:
        pass


def flush_langfuse() -> None:
    try:
        from langfuse import get_client

        get_client().flush()
    except Exception:
        pass
