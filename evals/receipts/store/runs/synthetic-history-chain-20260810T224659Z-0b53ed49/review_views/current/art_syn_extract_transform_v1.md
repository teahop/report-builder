# Current review — `art_syn_extract_transform_v1`

_Rebuildable view. Sources of truth: receipt, decisions.jsonl, evals.jsonl._

- run: `synthetic-history-chain-20260810T224659Z-0b53ed49`
- stage: `extract_transform`
- lineage: `evaluable`
- artifact SHA-256: `6ad896318ef33692d5d1eca36d96fc095e3fcb2325b9fa71d151183a31c56636`
- created_at: `2026-08-10T22:46:59Z` _(metadata; not in artifact hash)_
- review status: **accepted**
- latest decision: `accepted` · origin=`synthetic_test` · reviewer=`tj` / `engineer` · at 2026-08-10T22:46:59Z
- **Not human approval** — this is a synthetic_test / harness decision.
- decision notes: Accept transform output. [LOADED_INVALID_V1_IDENTITY]

## Parents

- `art_syn_extract_raw_v1` stage=`extract_raw` sha=`a0afde8b58cc…` required_accepted=True

## Configuration

- git_sha: `cb3d03cd6b3febf57a8fc65e2186926ae691a424`
- code_fingerprint: `synthetic-chain-v1`
- prompt_sha256: `None`
- structure_spec_id: `None`
- structure_spec_sha256: `None`
- model: `None` temperature=`None`

## Counts

- quarantined: **1**
- retained: **1**
- suppressed_duplicate: **1**
- transformed: **1**

## Dispositions

### By kind

- `quarantined`: 1
- `retained`: 1
- `suppressed_duplicate`: 1
- `transformed`: 1

### Notable items

- **transformed** · `syn:chunk:a89044594b18:raw:001` · normalize_medications
- **quarantined** · `syn:chunk:a89044594b18:raw:002` · spurious_future_grade
- **suppressed_duplicate** · `syn:chunk:a89044594b18:raw:003` · 

### Quarantine review items

- `q_syn_grade_future` ← `syn:chunk:a89044594b18:raw:002`: spurious_future_grade

## Append-only eval results

_Legacy v1 embedded eval_results (prefer evals.jsonl for new work):_
- `transform_total_accounting`@1: **pass** (items=[]) — {'retained': 1, 'transformed': 1, 'quarantined': 1, 'suppressed_duplicate': 1}

## Machine artifact paths

- machine_output: `by_sha/6ad896318ef33692d5d1eca36d96fc095e3fcb2325b9fa71d151183a31c56636.json` (sha `6ad896318ef3…`)
- deterministic_decisions: `by_sha/8440d200e920f71a05ad9a3d5454752fa75e65af923da8a419b8702e88017b26.json` (sha `8440d200e920…`)
- receipt: `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/receipts/art_syn_extract_transform_v1.json`
- current review (this file): `runs/synthetic-history-chain-20260810T224659Z-0b53ed49/review_views/current/art_syn_extract_transform_v1.md`

## Note on acceptance

- Accepted only under `synthetic_test` origin for gate mechanics.
- Does **not** claim human review of a real/approved-anonymized case.
