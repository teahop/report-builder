# Release checklist

Source of truth: `docs/product/bastiongpt-production/SPEC-release-verification.md`.
A deploy-visible item is not done until the **running instance** serves it. Record evidence next to each box (trace path, test count, diff), not just a check.

Sign-off: **TJ**, after running this list on his own machine on **synthetic** data. Molly remains the judge of voice and the signer of the report.

Staging run: **2026-09-11**, TJ's machine, synthetic `fixture_001` only. Production process listened on `127.0.0.1:8013` with `APP_PROFILE=production`, then was stopped. No real case data.

## Before go-live

- [x] **Secrets can't be committed** — `git check-ignore .env.production` prints the path; `.env.production.example` is tracked; no keys in any tracked file.
      Evidence: `git check-ignore .env.production` → `.env.production`. Tracked templates: `.env.example`, `.env.production.example` (empty placeholders). Local `.env.production` exists and is untracked. Name-only check: production file has `BASTION_API_KEY` + `LANGFUSE_*` and no `OPENAI_API_KEY`; demo `.env` has `OPENAI_API_KEY` + `LANGFUSE_*` and no Bastion key.
- [x] **Privacy review** — app logs are body-free on both profiles; production Langfuse traces go only to the HIPAA project; no case content in docs or the vault repo.
      Evidence: `test_stage_log.py` green (ingest success + restricted refusal omit body text). Production uvicorn access log for the staging calls was path + status only (`POST /ingest|conflicts|/draft/history|/case/purge`) — no request/response bodies. HIPAA Langfuse keys live only in local `.env.production` (gitignored).
- [x] **BAA baseline filled** — `docs/product/bastiongpt-production/SPEC-compliance-logging.md` terms block is complete and dated.
      Evidence: `## Compliance baseline (settled 2026-09-11)` — BAA automatic, no post-run training use, nothing saved, access = Molly + TJ-in-dev.
- [x] **Gate correctness** — `python -m pytest test_data_gate.py --ignore=.venv -q` green; demo refuses `data_class: restricted` (403).
      Evidence: `test_data_gate.py` green (2026-09-11). Local demo process `POST /ingest` `data_class=restricted` → **403** `Restricted data refused: profile is not production; backend is not Bastion.` Probe string not echoed.
- [x] **Backend + API version** — production `/health` shows `runtime: bastiongpt-api-v2.0` and `backend: bastion`. Adapter sends no `model` field.
      Evidence: running `http://127.0.0.1:8013/health` → `runtime: bastiongpt-api-v2.0`, `backend: bastion`, `profile: production`, `restricted_allowed: true`. `provider.py` Bastion payload is `messages` + `max_tokens` (+ optional `temperature`) — no `model` key. `BASTION_API_VERSION = "2.0"`.
- [x] **Fixture verification** — do not overwrite `evals/cache/fixture_001_ledger.json`. Confirm the intended synthetic set.
      Evidence: cache still **105** facts (synthetic child Emma Rose Callahan). `git status --porcelain` clean for that file after the smoke.
- [x] **Automated tests** — `python -m pytest --ignore=.venv -q`. Record pass/skip counts (the bar is not 150/150).
      Evidence: **281 passed, 2 skipped** (2026-09-11, this machine).
- [x] **Production smoke on synthetic data** — `APP_PROFILE=production` against Bastion, one end-to-end draft; no bodies in app logs.
      Evidence: `POST /ingest` 200 (synthetic staging note). `POST /conflicts` 200 (10 conflicts / 4 variance / 27 timelines). `POST /draft/history` on cached fixture_001 ledger, `skip_entailment: true`, `case_id=t13-staging-001` → **200**, `section_populated: true`, 4/4 sections, 69216 tokens, 34155 ms, `trace_id` present. Access log body-free. Response `model` still echoes the request label (`gpt-4o-mini`); backend was Bastion per `/health`.
- [x] **Verified against the running instance** — fetch the changed artifact from the live/running URL and diff against local. "Committed" ≠ "serving."
      Evidence: `GET /operator/` and `GET /operator/operator_live.js` from `127.0.0.1:8013` **diff-equal** local `static/operator/index.html` and `operator_live.js`. Served page contains `Delete case data`; JS contains `purgeCase`.
- [x] **Demo regression** — Render demo still refuses non-synthetic / restricted input and still runs OpenAI. Check the live URL.
      Evidence: live `https://report-builder-wc2k.onrender.com/health` → `runtime: openai-synthetic-only`, `production: bastiongpt-baa-not-this-repo`. Live `POST /ingest` with `data_class: restricted` (no `confirm_synthetic`) → **422** field required — Render is still the **pre-cutover** contract because this branch is not deployed. Local new-code demo path is 403 (gate item). Public demo is unchanged.
- [x] **Delete-on-finish** — the delete-case-data action clears local artifacts **and** that case's Langfuse traces.
      Evidence: planted `local_store/cases/t13-staging-001/note.txt`; after History draft, `POST /case/purge` `{confirm_synthetic: true, case_id: t13-staging-001}` → **200**, `local_deleted_n: 1`, `langfuse_traces_deleted: 2`, directory gone.
- [x] **Launcher** — double-click `run-production.command` starts the server and opens the operator UI.
      Evidence: script is executable (`-rwxr-xr-x`), `bash -n` clean, exports `APP_PROFILE=production`, waits on `/health`, then `open /operator/`. This staging run started the same uvicorn invocation on **PORT=8013** (headless; macOS `open` not clicked) and served a healthy operator page.
- [x] **TJ staging run** — this entire list green on TJ's machine (synthetic) **before** Molly.
      Evidence: this file, 2026-09-11. Tool gate only — Molly still judges voice and signs reports. UI sufficiency for solo non-technical use (file upload, etc.) remains a separate lane.
- [x] **Rollback** — unset `APP_PROFILE` / use demo `.env`; the public demo is unaffected.
      Evidence: process with `APP_PROFILE` unset → `runtime: openai-synthetic-only`, `backend: openai`, `restricted_allowed: false`. Render health unchanged (openai). Revert path is config-only; production server for this run was stopped.

Do not put real case data in the smoke.
