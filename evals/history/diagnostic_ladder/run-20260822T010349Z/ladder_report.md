INTERIM PARENT — extraction accepted-for-now (2026-08-19), not final; prose→trace alignment not run

# Diagnostic ladder report — extract → ledger → brief → writer

**Run:** `run-20260822T010349Z`
**Package:** positive History writer on a same-provider extract
**Provider:** openai · **Model:** gpt-4o-mini
**Extract calls:** 22 (temp 0.0)
**Writer calls:** 4 (temp 1.0)
**Facts in this ledger:** 129
**Did not overwrite** `evals/cache/fixture_001_ledger.json` (sha `2b534d0f7f7ba2486a40f03b275f1702157306cb0007b9a9f8fe5371c910d768`)
**This-run ledger sha:** `169845ee84cbc6b9a83b1c734a2ca76a09435ca0ab53794b2c76c1f0b14151c3`
**Receipts:** `bastion-full-ladder-20260822T010349Z-ec56fe2b`
**trace_alignment_status:** `not_run_diagnostic`

| Stage | What this run can establish | Current status |
|---|---|---|
| source → raw extraction | complete-case Bastion extract; raw text retained per chunk | 22 calls; interim-accepted |
| raw extraction → deterministic disposition | production extract gates applied | inspect extract/ and ledger.json |
| disposition → ledger | exact parent identifiable | interim-accepted; sha `169845ee84cbc6b9a83b1c734a2ca76a09435ca0ab53794b2c76c1f0b14151c3` |
| ledger → brief | compiled from this ledger, not the OpenAI cache | hashed in manifest |
| brief → prose | short prompt + Phase 1 examples | 4 writer calls; see assembled.md |
| prose → trace alignment | not exercised | `not_run_diagnostic` |
| chart composition | not exercised | table position marked |

HARD STOP. No retune. No sweep. Parent is interim-accepted, not final.
