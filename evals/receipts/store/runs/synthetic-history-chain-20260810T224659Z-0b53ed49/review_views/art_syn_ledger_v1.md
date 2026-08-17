# Stage review — `art_syn_ledger_v1`

- run: `synthetic-history-chain-20260810T224659Z-0b53ed49`
- stage: `ledger`
- lineage: `evaluable`
- artifact SHA-256: `42be5f25f7789e204124e242eea099682505c9b77b9ebf0640d89530c80c5a70`
- created_at: `2026-08-10T22:46:59Z` _(metadata; not in artifact hash)_
- review status: **unreviewed**
- latest decision: _unreviewed_

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

## Validation / eval results

- `ledger_known_facts`@1: **pass** (items=['f_syn_001', 'f_syn_002'])

## Machine artifact paths

- machine_output: `by_sha/42be5f25f7789e204124e242eea099682505c9b77b9ebf0640d89530c80c5a70.json` (sha `42be5f25f778…`)
- receipt: `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/receipts/art_syn_ledger_v1.json`

## Unresolved

- This artifact has **no** append-only review decision yet.
- It cannot be an evaluable downstream parent until `accepted`.
