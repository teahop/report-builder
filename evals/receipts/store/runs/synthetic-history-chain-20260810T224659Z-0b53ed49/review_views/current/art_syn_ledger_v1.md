# Current review — `art_syn_ledger_v1`

_Rebuildable view. Sources of truth: receipt, decisions.jsonl, evals.jsonl._

- run: `synthetic-history-chain-20260810T224659Z-0b53ed49`
- stage: `ledger`
- lineage: `evaluable`
- artifact SHA-256: `42be5f25f7789e204124e242eea099682505c9b77b9ebf0640d89530c80c5a70`
- created_at: `2026-08-10T22:46:59Z` _(metadata; not in artifact hash)_
- review status: **accepted**
- latest decision: `accepted` · origin=`synthetic_test` · reviewer=`tj` / `engineer` · at 2026-08-10T22:46:59Z
- **Not human approval** — this is a synthetic_test / harness decision.
- decision notes: Accept synthetic ledger. [LOADED_INVALID_V1_IDENTITY]

## Parents

- `art_syn_extract_transform_v1` stage=`extract_transform` sha=`6ad896318ef3…` required_accepted=True

## Configuration

- git_sha: `cb3d03cd6b3febf57a8fc65e2186926ae691a424`
- code_fingerprint: `synthetic-chain-v1`
- prompt_sha256: `None`
- structure_spec_id: `None`
- structure_spec_sha256: `None`
- model: `None` temperature=`None`

## Counts

- facts: **2**

## Dispositions

_No deterministic-decisions artifact attached._

## Append-only eval results

_Legacy v1 embedded eval_results (prefer evals.jsonl for new work):_
- `ledger_known_facts`@1: **pass** (items=['f_syn_001', 'f_syn_002'])

## Machine artifact paths

- machine_output: `by_sha/42be5f25f7789e204124e242eea099682505c9b77b9ebf0640d89530c80c5a70.json` (sha `42be5f25f778…`)
- receipt: `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/receipts/art_syn_ledger_v1.json`
- current review (this file): `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/review_views/current/art_syn_ledger_v1.md`

## Note on acceptance

- Accepted only under `synthetic_test` origin for gate mechanics.
- Does **not** claim human review of a real/approved-anonymized case.
