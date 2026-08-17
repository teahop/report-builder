# Current review — `art_syn_extract_raw_v1`

_Rebuildable view. Sources of truth: receipt, decisions.jsonl, evals.jsonl._

- run: `synthetic-history-chain-20260810T224659Z-0b53ed49`
- stage: `extract_raw`
- lineage: `evaluable`
- artifact SHA-256: `a0afde8b58cc4308106cbf4524ff0d7df158ccc2c51a88812a0c9cf2eb1763d8`
- created_at: `2026-08-10T22:46:59Z` _(metadata; not in artifact hash)_
- review status: **accepted**
- latest decision: `accepted` · origin=`synthetic_test` · reviewer=`tj` / `engineer` · at 2026-08-10T22:46:59Z
- **Not human approval** — this is a synthetic_test / harness decision.
- decision notes: Accept synthetic raw extraction for chain demo. [LOADED_INVALID_V1_IDENTITY]

## Parents

_No parents._

## Configuration

- git_sha: `cb3d03cd6b3febf57a8fc65e2186926ae691a424`
- code_fingerprint: `synthetic-chain-v1`
- prompt_sha256: `bf7e85303d7367c7e717e5177b288c422779cbe2f8038e26672667f55709bcac`
- structure_spec_id: `None`
- structure_spec_sha256: `None`
- model: `fake-extract-0` temperature=`0.0`

## Counts

- raw_items: **4**

## Dispositions

_No deterministic-decisions artifact attached._

## Append-only eval results

_Legacy v1 embedded eval_results (prefer evals.jsonl for new work):_
- `expected_claim_presence`@1: **pass** (items=['syn:chunk:a89044594b18:raw:000', 'syn:chunk:a89044594b18:raw:001']) — sleep + medications claims present

## Machine artifact paths

- machine_output: `by_sha/a0afde8b58cc4308106cbf4524ff0d7df158ccc2c51a88812a0c9cf2eb1763d8.json` (sha `a0afde8b58cc…`)
- receipt: `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/receipts/art_syn_extract_raw_v1.json`
- current review (this file): `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/review_views/current/art_syn_extract_raw_v1.md`

## Notes

Synthetic raw extraction — fake provider, no network.

## Note on acceptance

- Accepted only under `synthetic_test` origin for gate mechanics.
- Does **not** claim human review of a real/approved-anonymized case.
