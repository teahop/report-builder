# Stage review — `art_syn_brief_v1`

- run: `synthetic-history-chain-20260810T224659Z-0b53ed49`
- stage: `brief`
- lineage: `evaluable`
- artifact SHA-256: `58a85a2466538e0c0fea7d9f200f63cbc38a341b90185e6ff2d476eea53be06f`
- created_at: `2026-08-10T22:46:59Z` _(metadata; not in artifact hash)_
- review status: **unreviewed**
- latest decision: _unreviewed_

## Parents

- `art_syn_ledger_v1` stage=`ledger` sha=`42be5f25f778…` required_accepted=True

## Configuration

- git_sha: `cb3d03cd6b3febf57a8fc65e2186926ae691a424`
- code_fingerprint: `synthetic-chain-v1`
- prompt_sha256: `None`
- structure_spec_id: `provisional_tj_v1`
- structure_spec_sha256: `c319aa7210e597ea44d585cdfbef0a6ae8a95cc4ed6166ba5002cab42c251e39`
- model: `None` temperature=`None`

## Counts

- selected: **2**

## Dispositions

### By kind

- `selected`: 2

### Notable items

_No transformed/quarantined/duplicate/error items._

## Validation / eval results

- `brief_routing_accounting`@1: **pass** (items=[]) — {'selected': 2}

## Machine artifact paths

- machine_output: `by_sha/58a85a2466538e0c0fea7d9f200f63cbc38a341b90185e6ff2d476eea53be06f.json` (sha `58a85a246653…`)
- deterministic_decisions: `by_sha/226e907a32e19f0e7c6de57aa5852c4ed55bd075b5899cd9e41cc7350b73ed4c.json` (sha `226e907a32e1…`)
- receipt: `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/receipts/art_syn_brief_v1.json`

## Unresolved

- This artifact has **no** append-only review decision yet.
- It cannot be an evaluable downstream parent until `accepted`.
