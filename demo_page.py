"""Streamlit evals panel and History fixture runner for the Report Builder.

Run:
  streamlit run demo_page.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

from evals.panel_checks import (
    HISTORY_SMOKE_SCRIPT,
    REFERRAL_SMOKE_SCRIPT,
    WEEK1,
    display_prose,
    history_before_after,
    list_trace_files,
    load_taxonomy,
    load_trace,
    openai_key_present,
    score_history_record,
    score_referral_record,
    trace_kind,
    trace_metadata,
)

load_dotenv(WEEK1 / ".env")

WORKDIR = Path(__file__).resolve().parent
WORKDIR_CMD = "."
HISTORY_FIXTURE = WORKDIR / "fixtures" / "synthetic_history_case.json"
HEALTH_FIXTURE = WORKDIR / "fixtures" / "synthetic_health_conflict_case.json"
FIXTURE_001_MANIFEST = WORKDIR / "fixtures" / "fixture_001" / "manifest.json"


def _assemble_fixture_001() -> dict:
    """Ask-shaped payload from the per-file fixture_001 case."""

    man = json.loads(FIXTURE_001_MANIFEST.read_text(encoding="utf-8"))
    sources = []
    for f in man["files"]:
        fx = json.loads((FIXTURE_001_MANIFEST.parent / f["fixture"]).read_text(encoding="utf-8"))
        sources.append(fx["sources"][0])
    return {
        "confirm_synthetic": True,
        "section": man.get("section") or "history",
        "child": man["child"],
        "sources": sources,
        "model": "gpt-4o-mini",
    }

STAGES = [
    {
        "num": 1,
        "title": "History fixture",
        "serve": "uvicorn main:app --port 8000 --reload",
        "look_for": (
            "ReportSection with attributed `facts`, surfaced `conflicts`, "
            "`cost_usd`, and `age_years_expected`. Prefer the home UI at `/` "
            "for multi-source demos."
        ),
        "mode": "fixture",
        "fields": ["force_bad_age", "model", "fixture"],
        "dummy_model": "gpt-4o-mini",
    },
]


def build_question_payload(
    question: str,
    stage: dict,
    force_bad: bool,
    model: str | None,
) -> dict:
    payload: dict = {"question": question}
    if "force_bad" in stage["fields"]:
        payload["force_bad"] = force_bad
    if "model" in stage["fields"] and model:
        payload["model"] = model
    return payload


def load_fixture_payload(name: str, force_bad_age: bool, model: str | None) -> dict:
    if name == "fixture_001":
        payload = _assemble_fixture_001()
    else:
        path = HEALTH_FIXTURE if name == "health" else HISTORY_FIXTURE
        payload = json.loads(path.read_text(encoding="utf-8"))
    if force_bad_age:
        payload["force_bad_age"] = True
    if model:
        payload["model"] = model
    return payload


def call_ask(base_url: str, payload: dict) -> tuple[int, dict | str]:
    try:
        response = httpx.post(f"{base_url.rstrip('/')}/ask", json=payload, timeout=180.0)
        try:
            return response.status_code, response.json()
        except json.JSONDecodeError:
            return response.status_code, response.text
    except httpx.ConnectError:
        return 0, {"error": f"Cannot reach {base_url} — start the stage server first."}
    except httpx.HTTPError as exc:
        return 0, {"error": str(exc)}


def render_curl(base_url: str, payload: dict) -> str:
    body = json.dumps(payload)
    return (
        f'curl -s -X POST {base_url.rstrip("/")}/ask '
        f'-H "Content-Type: application/json" -d \'{body}\''
    )


def render_terminal_block(stage: dict, base_url: str, payload: dict) -> str:
    return f"""cd {WORKDIR_CMD}
source .venv/bin/activate
pip install -r requirements.txt
{stage["serve"]}

# In another terminal — test this stage:
{render_curl(base_url, payload)}"""


def _render_metadata(record: dict, *, show_status: bool = True) -> None:
    meta = trace_metadata(record)
    cols = st.columns(4)
    cols[0].metric("Tokens", meta.get("tokens_used") if meta.get("tokens_used") is not None else "—")
    cols[1].metric("Latency (ms)", meta.get("latency_ms") if meta.get("latency_ms") is not None else "—")
    cost = meta.get("cost_usd")
    cols[2].metric("Cost (USD)", f"{cost:.6f}" if isinstance(cost, (int, float)) else "—")
    cols[3].metric("Temp", meta.get("temperature") if meta.get("temperature") is not None else "—")
    prompt_sha = meta.get("prompt_sha256") or "—"
    if prompt_sha != "—" and len(str(prompt_sha)) > 12:
        prompt_sha = str(prompt_sha)[:12]
    voice_sha = meta.get("voice_store_sha") or "—"
    if voice_sha != "—" and len(str(voice_sha)) > 12:
        voice_sha = str(voice_sha)[:12]
    st.markdown(
        f"**Fixture:** `{meta.get('fixture_id') or '—'}` · "
        f"**Model:** `{meta.get('model') or '—'}` · "
        f"**Prompt SHA:** `{prompt_sha}` · "
        f"**Voice SHA:** `{voice_sha}`"
    )
    if show_status and meta.get("status"):
        st.caption(f"status: {meta['status']}")


def _render_check_rows(results) -> None:
    rows = [
        {
            "check": item.name,
            "result": "pass" if item.passed else "fail",
            "detail": item.detail,
        }
        for item in results
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def _render_trace_body(loaded) -> None:
    record = loaded.records[0] if loaded.records else {}
    if loaded.kind == "history":
        _render_metadata(record)
        results = score_history_record(record)
        st.markdown("**Offline History checks** (deterministic; diagnostic parent)")
        _render_check_rows(results)
        prose = display_prose(record, kind="history")
        st.markdown("**Prose**")
        st.text(prose or "(no prose in this trace)")
        return

    _render_metadata(record)
    if record.get("error") or record.get("observed_failure"):
        st.warning(record.get("observed_failure") or record.get("error"))
    results = score_referral_record(record)
    st.markdown("**Offline referral checks** (deterministic; no model call)")
    _render_check_rows(results)
    prose = display_prose(record, kind="referral")
    st.markdown("**Prose**")
    st.text(prose or "(no prose in this trace)")


def render_evals_panel() -> None:
    st.subheader("Evals — TRACE traces on disk")
    st.caption(
        "Display mode reads stored jsonl only. Zero model calls unless you "
        "explicitly run a smoke. Maven before/after is History: 8/7 coded 20-run vs the new writer sweep."
    )

    st.markdown("### Before / after — History DOB/age opener")
    comparison = history_before_after()
    opener = next(
        row for row in comparison.deltas if row["check"] == "no_dob_age_opener"
    )
    before_opener = next(
        item for item in comparison.before_results if item.name == "no_dob_age_opener"
    )
    after_opener = next(
        item for item in comparison.after_results if item.name == "no_dob_age_opener"
    )
    st.caption(
        f"Before: {comparison.before_label}. After: {comparison.after_label}. "
        "Top coded failure was History opening with DOB/age (20/20). "
        "The after-set is the positive History writer on a frozen Bastion ledger — "
        "extraction still not accepted."
    )
    metric_cols = st.columns(2)
    with metric_cols[0]:
        st.metric(
            "DOB/age opener (before)",
            f"{before_opener.n_pass if before_opener.n_pass is not None else 0}/{before_opener.n or 20}",
        )
    with metric_cols[1]:
        after_n = after_opener.n or 20
        after_pass = after_opener.n_pass if after_opener.n_pass is not None else (after_n if after_opener.passed else 0)
        st.metric(
            "DOB/age opener (after)",
            f"{after_pass}/{after_n}",
            delta=opener["delta"],
        )
    st.dataframe(
        [
            {
                "check": row["check"],
                "before": row["before"],
                "after": row["after"],
                "delta": row["delta"],
                "before_detail": row["before_detail"],
                "after_detail": row["after_detail"],
            }
            for row in comparison.deltas
        ],
        hide_index=True,
        use_container_width=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Before** {comparison.before_label}")
        if comparison.before_record is not None:
            _render_metadata(comparison.before_record, show_status=False)
            sample = display_prose(comparison.before_record, kind="history") or "(no prose)"
            st.text(sample[:1600] + ("…" if len(sample) > 1600 else ""))
        else:
            st.caption("No baseline sample on disk.")
    with right:
        st.markdown(f"**After** `{comparison.after_label}`")
        if comparison.after_record is not None:
            _render_metadata(comparison.after_record, show_status=False)
            sample = display_prose(comparison.after_record, kind="history") or "(no prose)"
            st.text(sample[:1600] + ("…" if len(sample) > 1600 else ""))
        else:
            st.warning("No History after-set on disk yet.")

    st.markdown("### Trace browser")
    traces = list_trace_files()
    if not traces:
        st.info("No `*.jsonl` traces under evals/traces, evals/referral/traces, or evals/history/traces.")
    else:
        labels = [
            f"{trace_kind(p)} / {p.name}"
            for p in traces
        ]
        choice = st.selectbox("Stored trace", options=list(range(len(traces))), format_func=lambda i: labels[i])
        _render_trace_body(load_trace(traces[choice]))

    st.markdown("### Failure taxonomy")
    taxonomy = load_taxonomy()
    st.caption(f"Source: {taxonomy.get('source', '—')}")
    if taxonomy.get("instruction"):
        st.caption(taxonomy["instruction"])
    st.table(taxonomy.get("rows") or [])
    st.caption(
        "These categories come from the 8/7 open-coding pass (before). "
        "Do not treat the after-set phrase tripwire as a replacement for that coding."
    )

    st.markdown("### Run a smoke")
    st.caption(
        "History smoke is the after-set for this homework. Referral smoke stays available. "
        "Display mode works with no key."
    )
    if openai_key_present():
        hist_col, ref_col = st.columns(2)
        with hist_col:
            if st.button("Run history smoke", type="primary"):
                with st.spinner("Running one History smoke…"):
                    completed = subprocess.run(
                        [sys.executable, str(HISTORY_SMOKE_SCRIPT)],
                        cwd=str(WEEK1),
                        capture_output=True,
                        text=True,
                        env=os.environ.copy(),
                        check=False,
                    )
                output = (completed.stdout or "") + (completed.stderr or "")
                st.code(output[-4000:] if output else "(no output)")
                if completed.returncode == 0:
                    st.success("History smoke finished. New jsonl is in evals/history/traces/.")
                else:
                    st.error(f"History smoke exited {completed.returncode}. Do not sweep.")
        with ref_col:
            if st.button("Run referral smoke", type="secondary"):
                with st.spinner("Running one synthetic referral smoke…"):
                    completed = subprocess.run(
                        [sys.executable, str(REFERRAL_SMOKE_SCRIPT)],
                        cwd=str(WEEK1),
                        capture_output=True,
                        text=True,
                        env=os.environ.copy(),
                        check=False,
                    )
                output = (completed.stdout or "") + (completed.stderr or "")
                st.code(output[-4000:] if output else "(no output)")
                if completed.returncode == 0:
                    st.success("Referral smoke finished. New jsonl is in evals/referral/traces/.")
                else:
                    st.error(f"Referral smoke exited {completed.returncode}. Do not sweep.")
    else:
        st.button("Run history smoke", disabled=True)
        st.button("Run referral smoke", disabled=True)
        st.info(
            "OPENAI_API_KEY is unset — display mode only. From the repo root with a loaded `.env`:\n\n"
            "`python evals/history/run_smoke.py`  (new History after-set)\n\n"
            "`python evals/referral/run_smoke.py`"
        )


st.set_page_config(page_title="Report Builder evals", layout="wide")
st.title("Report Builder — fixture runner and evals")
st.caption(
    "Posts a synthetic History fixture to `main`. "
    "Evals reads stored TRACE jsonl with no model calls. "
    "For the multi-source UI, open http://127.0.0.1:8000/ after starting `uvicorn main:app`."
)

base_url = st.sidebar.text_input("API base URL", "http://127.0.0.1:8000")

st.sidebar.markdown("### Run this page")
st.sidebar.code(
    f"cd {WORKDIR_CMD}\nsource .venv/bin/activate\nstreamlit run demo_page.py",
    language="bash",
)

tabs = st.tabs([f"Demo {s['num']}: {s['title']}" for s in STAGES] + ["Evals"])

for tab, stage in zip(tabs[:-1], STAGES):
    with tab:
        st.subheader(f"Demo {stage['num']} — {stage['title']}")
        st.markdown(f"**Look for:** {stage['look_for']}")

        force_bad = stage.get("dummy_force_bad", False)
        force_bad_age = False
        model = stage.get("dummy_model")
        fixture_choice = "history"

        if stage["mode"] == "question":
            default_q = stage["dummy_question"]
            stage_question = st.text_input(
                "Question",
                default_q,
                key=f"q_{stage['num']}",
                placeholder="Type a question to send to /ask…",
            )
            if "force_bad" in stage["fields"]:
                force_bad = st.checkbox(
                    "force_bad (break schema on attempt 1)",
                    value=stage.get("dummy_force_bad", False),
                    key=f"bad_{stage['num']}",
                )
            if "model" in stage["fields"]:
                options = [None, "gpt-4o", "gpt-4o-mini", "o3-mini"]
                default_model = stage.get("dummy_model")
                model = st.selectbox(
                    "model",
                    options,
                    index=options.index(default_model) if default_model in options else 0,
                    format_func=lambda m: m or "gpt-4o (default)",
                    key=f"model_{stage['num']}",
                )
            payload = build_question_payload(stage_question, stage, force_bad, model)
        else:
            fixture_choice = st.selectbox(
                "Fixture",
                ["history", "health", "fixture_001"],
                format_func=lambda n: {
                    "history": "synthetic_history_case.json",
                    "health": "synthetic_health_conflict_case.json",
                    "fixture_001": "fixture_001 (E.C. per-file case)",
                }[n],
                key=f"fixture_{stage['num']}",
            )
            if "force_bad_age" in stage["fields"]:
                force_bad_age = st.checkbox(
                    "force_bad_age (plant wrong age on attempt 0)",
                    value=False,
                    key=f"bad_age_{stage['num']}",
                )
            if "model" in stage["fields"]:
                options = [None, "gpt-4o", "gpt-4o-mini", "o3-mini"]
                default_model = stage.get("dummy_model")
                model = st.selectbox(
                    "model",
                    options,
                    index=options.index(default_model) if default_model in options else 0,
                    format_func=lambda m: m or "gpt-4o (default)",
                    key=f"model_{stage['num']}",
                )
            payload = load_fixture_payload(fixture_choice, force_bad_age, model)
            st.markdown(
                f"**Sources in fixture:** {len(payload.get('sources', []))} "
                f"(open `/` for the multi-source GUI)."
            )

        st.markdown("**Copy & run (terminal 1 — server, terminal 2 — curl):**")
        st.code(render_terminal_block(stage, base_url, payload), language="bash")

        if st.button("Run test", key=f"run_{stage['num']}", type="primary"):
            with st.spinner("Calling /ask..."):
                status, data = call_ask(base_url, payload)
            if status:
                st.markdown(f"**HTTP {status}**")
            st.json(data)

with tabs[-1]:
    render_evals_panel()

st.sidebar.divider()
st.sidebar.markdown(
    "**Product UI:** `uvicorn main:app` → http://127.0.0.1:8000/\n\n"
    "**Docs:** `README.md`"
)
