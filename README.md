# Report Builder

A drafting service for a Licensed Educational Psychologist's evaluation reports.
Typed case documents go in; a validated, fully attributed report section comes out.
She reviews and signs — the tool drafts, never decides.

**Provenance.** Extracted 2026-08-17 from [`teahop/AI-Internship`](https://github.com/teahop/AI-Internship) at `16090cd8ceab93c755bb4a6878829b09ec0d6fa9` (`ai-engineering-bootcamp-v2/week-1/`). Fresh history starts here; per-file history remains in that archive. All fixtures are synthetic (`DECISIONS.md` 2026-08-17).

## Compliance: OpenAI ≠ BastionGPT

| Runtime | What it is | What data it may see |
|---------|------------|----------------------|
| **This repo (OpenAI via `OPENAI_API_KEY`)** | Learning / build sandbox | **Synthetic / de-identified fixtures only** |
| **BastionGPT (BAA)** | Production drafting for real cases | Covered under your BAA — **not this repo** |

Every request must set `"confirm_synthetic": true`. Missing/false → refuse before any model call.
Nothing is persisted — the ledger is returned to the caller, never stored.

## Architecture

```
sources → /extract → LEDGER + gap_report + timelines
              ↓
         /conflicts  (deterministic — no model call)
              ↓
     briefs (compiled, no model)
              ↓
    /draft/history → History package + voice gate + review
```

| Stage | Endpoint | Model? | Output |
|-------|----------|--------|--------|
| Classify | `POST /ingest` | 1 cheap call | `{source_type, source_date, label, doc_class}` for **user confirmation** (never silent) |
| Extract | `POST /extract` | 1 call / new narrative source | `Ledger` (merged), `GapReport`, `timelines` (computed view) |
| Conflicts | `POST /conflicts` | none | record `conflicts`, perspectival `variance`, timelines |
| Briefs | `POST /draft/history/plan` | none | compiled per-section case briefs (inspectable; no model) |
| Draft | `POST /draft/history` | one call per populated section + entailment | History package + voice gate + review |
| Referral draft | `POST /draft/referral` | 0 if incomplete; else 1 draft call | Reason for Referral prose **or** typed context-completion items |
| Ask | `POST /ask` | full pipeline | Course contract: `answer`, `tokens_used`, `cost_usd` (internally `/draft/history`) |

`/ask` keeps its request/response shape, but internally runs extract → conflicts → `/draft/history`. Legacy `POST /draft` is retired.

The ruling ledger (`DECISIONS.md`) stays in the parent workspace, outside this repository, by design; `voice_store.json` is what ships. Runtime `/memory` treats a missing ledger as local-by-design.

## Setup

```bash
cp .env.example .env   # set OPENAI_API_KEY — synthetic use only
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Local run

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

| URL | What you get |
|-----|----------------|
| http://127.0.0.1:8000/ | Demo UI — pipeline stages visible before prose |
| http://127.0.0.1:8000/memory | Voice-gate store and write-then-recall (read-only; no API key) |
| https://ai-internship-c7lr.onrender.com/memory | Same page on the public deploy |
| http://127.0.0.1:8000/docs | OpenAPI |
| http://127.0.0.1:8000/health | Liveness |

Evals panel (optional): `streamlit run demo_page.py`

## Tests

```bash
python -m pytest --ignore=.venv -q
```

Baseline at extraction (WP1, 2026-08-17): **150 collected, 147 passed, 3 pre-existing failures** (missing Case 005 cache; `test_live_current_state_has_zero_human_progress` vs seven recorded `doc_11_chunk04` judgments). Do not treat 150/150 as the current bar.

## Memory (voice-gate store)

Public page: [https://ai-internship-c7lr.onrender.com/memory](https://ai-internship-c7lr.onrender.com/memory). Terminal proof: `python prove_voice_recall.py`.

**What do I keep?** Class A only — what Molly stated. Eight records, A1–A8. The *positive* voice is the phase-1 few-shot registry (`history_fewshots/phase1/`).

**When do I write it?** Recompiled from workspace `DECISIONS.md`. This service has no write endpoint.

**Where does it live?** `voice_store.json`, version-controlled beside the code.

**How do I get it back?** `evaluate_voice_gates` loads the store from disk at review time. Cross-session proof: `python voice_store.py`, then `python voice_recall.py <draft.json>` — the recall argv never contains the rule text.

## Reason for Referral (`POST /draft/referral`)

```bash
curl -s -X POST "${SERVICE_URL:-http://127.0.0.1:8000}/draft/referral" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm_synthetic": true,
    "ledger": {
      "child": {
        "name": "Jordan Lee Quinn",
        "dob": "2015-06-01",
        "evaluation_date": "2026-03-15"
      },
      "ledger_version": "1",
      "built_at": "2026-03-15T12:00:00Z",
      "sources": [],
      "facts": []
    },
    "context": {
      "evaluation_type": {
        "context_id": "ctx_et_1",
        "normalized_value": "private_psychoeducational_evaluation",
        "capture_method": "clinician_entered",
        "confirmation_state": "confirmed"
      },
      "requested_by": [{
        "context_id": "ctx_req_1",
        "name": "Avery Quinn",
        "role": "parent",
        "capture_method": "clinician_entered",
        "confirmation_state": "confirmed"
      }],
      "referral_trigger": {
        "context_id": "ctx_trig_1",
        "normalized_value": "clarify developmental and behavioral concerns",
        "capture_method": "clinician_entered",
        "confirmation_state": "confirmed"
      },
      "client_goals": [{
        "context_id": "ctx_goal_1",
        "raw_text": "We want to understand what supports will actually help.",
        "presentation_mode": "paraphrase",
        "capture_method": "client_reported",
        "confirmation_state": "confirmed"
      }],
      "suspected_disabilities": [{
        "context_id": "ctx_sd_1",
        "category": "other_health_impairment",
        "capture_method": "clinician_confirmed",
        "confirmation_state": "confirmed"
      }]
    }
  }' | python3 -m json.tool
```

History smoke (cached fixture_001 ledger): `python evals/history/run_smoke.py`

## Layout

```
.
├── main.py                 # /ingest /extract /conflicts /draft/history /draft/referral /ask /memory
├── extract.py / conflicts.py / draft.py / ingest.py / coverage.py / derived.py
├── history_draft.py / history_compiler.py / history_api.py / draft_output.py
├── voice_store.py / voice_store.json
├── voice_recall.py / prove_voice_recall.py
├── memory_api.py / static/memory.html
├── history_fewshots/       # phase-1 approved excerpts (positive voice channel)
├── schemas.py / predicates.py / validators.py / draft_validators.py
├── provider.py             # sole OpenAI client import (default); Bastion opt-in
├── static/index.html       # pipeline-visible demo UI
├── fixtures/               # synthetic cases + sibling expected_* fields
├── extract_prompt.md / history_policy.md / history_writer_prompt.md / referral_prompt.md
├── evals/                  # harness + STATUS-cited evidence (not homework bulk)
└── test_*.py
```
