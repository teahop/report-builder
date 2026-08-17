# Stage review — `art_syn_extract_raw_v1`

- run: `synthetic-history-chain-20260810T224659Z-0b53ed49`
- stage: `extract_raw`
- lineage: `evaluable`
- artifact SHA-256: `a0afde8b58cc4308106cbf4524ff0d7df158ccc2c51a88812a0c9cf2eb1763d8`
- created_at: `2026-08-10T22:46:59Z` _(metadata; not in artifact hash)_
- review status: **unreviewed**
- latest decision: _unreviewed_

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

## Tokens / cost

- total_tokens: `42`

## Dispositions

_No deterministic-decisions artifact attached._

## Validation / eval results

- `expected_claim_presence`@1: **pass** (items=['syn:chunk:a89044594b18:raw:000', 'syn:chunk:a89044594b18:raw:001']) — sleep + medications claims present

## Machine artifact paths

- machine_output: `by_sha/a0afde8b58cc4308106cbf4524ff0d7df158ccc2c51a88812a0c9cf2eb1763d8.json` (sha `a0afde8b58cc…`)
- receipt: `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/receipts/art_syn_extract_raw_v1.json`

## Notes

Synthetic raw extraction — fake provider, no network.

## Unresolved

- This artifact has **no** append-only review decision yet.
- It cannot be an evaluable downstream parent until `accepted`.
