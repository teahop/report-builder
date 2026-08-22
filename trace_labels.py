"""Trace labeling — one vocabulary for every run that reaches Langfuse.

Why this module exists: Langfuse v4 sets trace-level attributes through
``propagate_attributes``, which stamps the active span *and* every child span
created inside the context. The v3 call it replaced
(``get_client().update_current_trace(...)``) no longer exists, and the one place
that used it swallowed the ``AttributeError`` — so sweeps ran unlabeled for
weeks without complaining. Labeling lives here so the vocabulary cannot drift
between runners and a broken label is loud rather than silent.

The label set is deliberately the identity a run already carries in its manifest
and JSONL row: which sweep, which prompt version, which fixture, which parent
ledger, which commit. Metadata values are coerced to strings by Langfuse and
capped at 200 characters, so hashes belong here and prose does not.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

# `environment` separates the kinds of traffic that otherwise pile up in one
# undifferentiated Langfuse project. There is no "production" here in the usual
# sense — there is controlled eval work, there is TJ or an agent driving the code
# from Claude Code / a terminal / Cursor, there is someone clicking the deployed
# Render interface, and there are tests. Only the first is a measurement.
ENV_EVAL = "eval"
ENV_LOCAL = "local"
ENV_RENDER = "render"
ENV_TEST = "test"

# `local` and `render` run the same code, so the router cannot tell them apart on
# its own — the deployment says which it is. Render sets RENDER=true in its own
# environment; LANGFUSE_TRACING_ENVIRONMENT overrides both when set explicitly.


def app_environment() -> str:
    """Which non-eval world this process is running in."""

    explicit = os.getenv("LANGFUSE_TRACING_ENVIRONMENT")
    if explicit:
        return explicit
    if os.getenv("PYTEST_CURRENT_TEST"):
        return ENV_TEST
    if os.getenv("RENDER"):
        return ENV_RENDER
    return ENV_LOCAL


# Langfuse coerces metadata values to str and drops any longer than this.
_MAX_VALUE_CHARS = 200

_REPO = Path(__file__).resolve().parent

_warned: set[str] = set()


def _warn_once(message: str) -> None:
    if message in _warned:
        return
    _warned.add(message)
    print(f"trace_labels: {message}", file=sys.stderr)


def git_sha(*, short: bool = True) -> str | None:
    """Current commit of the report-builder repo, or None outside a checkout."""

    args = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
    try:
        return subprocess.check_output(
            args, cwd=_REPO, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_is_dirty() -> bool | None:
    """True when the working tree has uncommitted changes; None if unknown.

    A sweep run on a dirty tree carries a commit label that does not describe
    what actually ran, so runners surface this rather than hiding it.
    """

    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=_REPO, stderr=subprocess.DEVNULL, text=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(out.strip())


def clean_metadata(metadata: dict[str, Any] | None) -> dict[str, str]:
    """Drop None, stringify, truncate — what survives Langfuse's own coercion."""

    cleaned: dict[str, str] = {}
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        text = value if isinstance(value, str) else str(value)
        cleaned[str(key)] = text[:_MAX_VALUE_CHARS]
    return cleaned


def clean_tags(tags: list[str] | tuple[str, ...] | None) -> list[str]:
    """Deduplicate, preserve order, drop empties."""

    seen: list[str] = []
    for tag in tags or ():
        text = str(tag).strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def _propagation_context(
    *,
    session_id: str | None,
    tags: list[str],
    environment: str | None,
    version: str | None,
    metadata: dict[str, str],
) -> Any:
    try:
        from langfuse import propagate_attributes
    except ImportError:
        # Langfuse not installed — drafting still works, tracing is a no-op.
        return contextlib.nullcontext()
    except Exception as exc:  # pragma: no cover - defensive
        _warn_once(f"could not import propagate_attributes ({exc!r}); runs will be unlabeled")
        return contextlib.nullcontext()

    kwargs: dict[str, Any] = {}
    if session_id:
        kwargs["session_id"] = session_id[:_MAX_VALUE_CHARS]
    if tags:
        kwargs["tags"] = tags
    if environment:
        kwargs["environment"] = environment
    if version:
        kwargs["version"] = version[:_MAX_VALUE_CHARS]
    if metadata:
        kwargs["metadata"] = metadata

    try:
        return propagate_attributes(**kwargs)
    except Exception as exc:
        _warn_once(f"propagate_attributes rejected the label set ({exc!r}); runs will be unlabeled")
        return contextlib.nullcontext()


@contextlib.contextmanager
def label_run(
    *,
    session_id: str | None = None,
    tags: list[str] | tuple[str, ...] | None = None,
    environment: str = ENV_EVAL,
    version: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Stamp the active trace and every span created inside this context.

    Call it as early as possible inside the ``@observe``-decorated entrypoint —
    spans that already exist are not updated retroactively, and a span without
    the attribute is excluded from any aggregate filtered on it.

    Args:
        session_id: Groups the runs of one sweep. Use the eval run id.
        tags: Coarse filters — stage, package, provider, fixture.
        environment: ``ENV_EVAL`` for controlled runs, ``app_environment()`` for the app.
        version: Commit sha, so a cohort can be tied to the code that made it.
        metadata: Fine-grained identity — prompt hashes, spec ids, ledger sha.
    """

    with _propagation_context(
        session_id=session_id,
        tags=clean_tags(tags),
        environment=environment,
        version=version if version is not None else git_sha(),
        metadata=clean_metadata(metadata),
    ):
        yield


def current_trace_ids() -> tuple[str | None, str | None]:
    """(trace_id, trace_url) for the active trace, or (None, None)."""

    try:
        from langfuse import get_client

        lf = get_client()
        trace_id = lf.get_current_trace_id()
        url = lf.get_trace_url(trace_id=trace_id) if trace_id else None
        return trace_id, url
    except Exception:
        return None, None
