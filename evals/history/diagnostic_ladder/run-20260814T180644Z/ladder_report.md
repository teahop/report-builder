DIAGNOSTIC ONLY — UPSTREAM EXTRACTION/LEDGER NOT ACCEPTED

# Diagnostic ladder report — extract → ledger → brief → writer

**Run:** `run-20260814T180644Z`
**Package:** positive History writer on a same-provider extract
**Provider:** bastion · **Model:** bastiongpt-auto
**Extract calls:** 21 (temp 0.0)
**Writer calls:** 4 (temp 1.0)
**Facts in this ledger:** 241
**Did not overwrite** `evals/cache/fixture_001_ledger.json` (sha `1aa5f1b180002983aaf15fa797f7bce9faf159456291e0f00a8b1fe1953df7db`)
**This-run ledger sha:** `3d5cab82253d220f5a5adf1e2ded487c3ea1b02ac63836beaff361df77b89370`
**Receipts:** `bastion-full-ladder-20260814T180644Z-7f30277e`
**trace_alignment_status:** `not_run_diagnostic`

| Stage | What this run can establish | Current status |
|---|---|---|
| source → raw extraction | complete-case Bastion extract; raw text retained per chunk | 21 calls; unaccepted |
| raw extraction → deterministic disposition | production extract gates applied | inspect extract/ and ledger.json |
| disposition → ledger | exact parent identifiable | provisional / not accepted; sha `3d5cab82253d220f5a5adf1e2ded487c3ea1b02ac63836beaff361df77b89370` |
| ledger → brief | compiled from this ledger, not the OpenAI cache | hashed in manifest |
| brief → prose | short prompt + Phase 1 examples | 4 writer calls; see assembled.md |
| prose → trace alignment | not exercised | `not_run_diagnostic` |
| chart composition | not exercised | table position marked |

HARD STOP. No retune. No sweep. Ledger not accepted.
