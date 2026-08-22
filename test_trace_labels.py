"""Trace labeling contract.

The bug these guard against: labeling was written against the v3 call
``get_client().update_current_trace(...)``, wrapped in a bare ``except``. The v4
upgrade removed that method, so every sweep ran unlabeled and nothing said so.
"""

from __future__ import annotations

import pytest

import trace_labels
from trace_labels import ENV_APP, ENV_EVAL, clean_metadata, clean_tags, label_run


def test_langfuse_still_exposes_the_call_we_label_through() -> None:
    """Fail loudly on the next SDK major, instead of silently unlabeling runs."""

    langfuse = pytest.importorskip("langfuse")
    assert hasattr(langfuse, "propagate_attributes")


def test_clean_metadata_drops_none_and_truncates() -> None:
    cleaned = clean_metadata(
        {"kept": "value", "dropped": None, "numeric": 3, "long": "x" * 500}
    )
    assert cleaned == {"kept": "value", "numeric": "3", "long": "x" * 200}


def test_clean_tags_dedupes_and_preserves_order() -> None:
    assert clean_tags(["eval", "history", "eval", "  ", "bastion"]) == [
        "eval",
        "history",
        "bastion",
    ]


def test_label_run_forwards_the_label_set(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Recorder:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *exc: object) -> bool:
            return False

    def fake_propagate(**kwargs: object) -> _Recorder:
        captured.update(kwargs)
        return _Recorder()

    monkeypatch.setattr("langfuse.propagate_attributes", fake_propagate)

    with label_run(
        session_id="sweep-1",
        tags=["eval", "history"],
        environment=ENV_EVAL,
        version="abc1234",
        metadata={"writer_prompt_hash": "deadbeef", "run_index": 3, "skipped": None},
    ):
        pass

    assert captured["session_id"] == "sweep-1"
    assert captured["tags"] == ["eval", "history"]
    assert captured["environment"] == "eval"
    assert captured["version"] == "abc1234"
    assert captured["metadata"] == {"writer_prompt_hash": "deadbeef", "run_index": "3"}


def test_label_run_defaults_version_to_the_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Recorder:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *exc: object) -> bool:
            return False

    monkeypatch.setattr(
        "langfuse.propagate_attributes",
        lambda **kwargs: (captured.update(kwargs), _Recorder())[1],
    )
    monkeypatch.setattr(trace_labels, "git_sha", lambda **_: "cafe123")

    with label_run(session_id="sweep-2", tags=["eval"], environment=ENV_APP):
        pass

    assert captured["version"] == "cafe123"


def test_label_run_is_a_no_op_when_propagation_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A broken label must not take a 20-run sweep down with it — but must say so."""

    def boom(**_: object) -> None:
        raise RuntimeError("no")

    monkeypatch.setattr("langfuse.propagate_attributes", boom)
    trace_labels._warned.clear()

    ran = False
    with label_run(session_id="sweep-3", tags=["eval"]):
        ran = True

    assert ran
    assert "unlabeled" in capsys.readouterr().err


def test_label_run_does_not_swallow_body_errors() -> None:
    with pytest.raises(ValueError):
        with label_run(session_id="sweep-4", tags=["eval"]):
            raise ValueError("from the body")
