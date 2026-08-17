# Current review — `art_extract_audit_replay_v2`

_Rebuildable view. Sources of truth: receipt, decisions.jsonl, evals.jsonl._

- run: `extract-audit-replay-20260810T231331Z-6b58509e`
- stage: `diagnostic_replay`
- lineage: `diagnostic_replay`
- artifact SHA-256: `f1d7e977d46f21fc8ec11d3058e390ff6a1cff49a603af2c071d77458e65fdf3`
- created_at: `2026-08-10T23:13:31Z` _(metadata; not in artifact hash)_
- review status: **unreviewed**
- latest decision: _unreviewed_
- immutable evidence view: `by_sha/b3569212e0b666dc829e40b74501b60993a43e37f8825fbe78e0a92a10ae3469.md` (sha `b3569212e0b6…`)

## Parents

_No parents._

## Configuration

- git_sha: `cb3d03cd6b3febf57a8fc65e2186926ae691a424`
- code_fingerprint: `None`
- prompt_sha256: `9096284e4c0acabd32ad53f8194035f5cd678bb3156f2315e88e0b4719aba7a1`
- structure_spec_id: `None`
- structure_spec_sha256: `None`
- model: `gpt-4o-mini` temperature=`0.0`

## Counts

- chunks: **8**
- observed_silent_drop: **6**
- raw_items: **70**
- retained: **53**
- transformed: **11**

## Dispositions

### By kind

- `observed silent drop`: 6
- `retained`: 53
- `transformed`: 11

### Notable items

- **transformed** · `doc_11:chunk:9a3d5d2298aa:raw:003:8ae1b9ab05b1` · normalize_value · gate=`normalize`
- **observed silent drop** · `doc_11:chunk:fc9b786c086b:raw:002:8ca9bbc0d5e7` · spurious_grade · gate=`_draft_is_skippable`
- **transformed** · `doc_11:chunk:fc9b786c086b:raw:003:2594f79ca9d0` · normalize_value · gate=`normalize`
- **transformed** · `doc_11:chunk:fc9b786c086b:raw:007:64759362d39e` · normalize_value · gate=`normalize`
- **observed silent drop** · `doc_11:chunk:6fa5cd841ec5:raw:002:4fdaa774f27e` · spurious_grade · gate=`_draft_is_skippable`
- **observed silent drop** · `doc_11:chunk:6fa5cd841ec5:raw:004:7b3ffd6d549a` · spurious_attendance · gate=`_draft_is_skippable`
- **transformed** · `doc_25:chunk:a78ed6a8ceb7:raw:004:ef319111a4c8` · normalize_value · gate=`normalize`
- **transformed** · `doc_25:chunk:a78ed6a8ceb7:raw:005:66d6d33c78be` · normalize_value · gate=`normalize`
- **transformed** · `doc_25:chunk:feafb23c57fb:raw:007:c46351cde9f7` · normalize_value · gate=`normalize`
- **observed silent drop** · `doc_25:chunk:feafb23c57fb:raw:008:6d6e2e6aa2cd` · spurious_attendance · gate=`_draft_is_skippable`
- **transformed** · `doc_25:chunk:feafb23c57fb:raw:009:39278a852365` · normalize_value · gate=`normalize`
- **transformed** · `doc_25:chunk:2dde18755f5f:raw:003:90696c9fcb21` · normalize_value · gate=`normalize`
- **transformed** · `doc_25:chunk:2dde18755f5f:raw:004:afb1c48ad68e` · normalize_value · gate=`normalize`
- **observed silent drop** · `doc_25:chunk:2dde18755f5f:raw:005:4b42d062c5fa` · spurious_attendance · gate=`_draft_is_skippable`
- **transformed** · `doc_25:chunk:c70e8192a71c:raw:002:5937d2238e82` · normalize_value · gate=`normalize`
- **observed silent drop** · `doc_26:chunk:481263420851:raw:002:9c21b13caf95` · spurious_developmental_history · gate=`_draft_is_skippable`
- **transformed** · `doc_26:chunk:481263420851:raw:008:8b7e3053255b` · normalize_value · gate=`normalize`

### Acceptance blocker

- This artifact contains **observed silent drop** items.
- It cannot become an accepted evaluable parent until a new run gives every item a valid evaluable disposition (quarantine / not_draftable / retained / …).

## Append-only eval results

_All recorded versions are listed; nothing is silently collapsed._

- `extract_total_accounting`@1: **pass** · sha=`f1d7e977d46f…` · recorded `2026-08-10T23:13:31Z` · evaluator=`receipt_indexer` origin=`system` — accounted 70 raw items; 6 observed_silent_drop
- `not_parent_of_legacy_cache`@1: **pass** · sha=`f1d7e977d46f…` · recorded `2026-08-10T23:13:31Z` · evaluator=`receipt_indexer` origin=`system` — legacy marker art_legacy_fixture_001_ledger recorded separately; not listed as parent of diagnostic replay

## Machine artifact paths

- machine_output: `by_sha/f1d7e977d46f21fc8ec11d3058e390ff6a1cff49a603af2c071d77458e65fdf3.json` (sha `f1d7e977d46f…`)
- deterministic_decisions: `by_sha/e45c49fdac979595f6316899203eb92185434643edd4860f82341173f86c69fd.json` (sha `e45c49fdac97…`)
- evidence_view: `by_sha/b3569212e0b666dc829e40b74501b60993a43e37f8825fbe78e0a92a10ae3469.md` (sha `b3569212e0b6…`)
- receipt: `runs/extract-audit-replay-20260810T231331Z-6b58509e/receipts/art_extract_audit_replay_v2.json`
- current review (this file): `runs/extract-audit-replay-20260810T231331Z-6b58509e/review_views/current/art_extract_audit_replay_v2.md`

## Notes

Targeted chunk replay indexed as diagnostic_replay. Gate skips recorded as observed_silent_drop (historical truth). Not the parent of art_legacy_fixture_001_ledger / fixture_001_ledger.json. Cannot become an accepted evaluable parent until a new run accounts for every item with a valid evaluable disposition.

## Human-readable item comparisons

_Navigation only — rebuildable. Does not change receipt or evidence hashes._

- **Origin:** `targeted_chunk_replay` (temperature-0 re-extract of selected chunks).
- **Not** the original 2026-08-10 Langfuse generations.
- **Not** the parent of the legacy 77-fact cache (`legacy_untraceable`).
- **Extraction content remains unreviewed** at the artifact level until a human records an artifact decision.

- [Item comparison README](../../../../../../history/extraction_audit/item_comparison/README.md)
- **Start here:** [`doc_11_chunk04.md`](../../../../../../history/extraction_audit/item_comparison/doc_11_chunk04.md) — seven-item review slice
- [`doc_11_chunk01.md`](../../../../../../history/extraction_audit/item_comparison/doc_11_chunk01.md)
- [`doc_11_chunk02.md`](../../../../../../history/extraction_audit/item_comparison/doc_11_chunk02.md)
- [`doc_11_chunk04.md`](../../../../../../history/extraction_audit/item_comparison/doc_11_chunk04.md)
- [`doc_25_chunk00.md`](../../../../../../history/extraction_audit/item_comparison/doc_25_chunk00.md)
- [`doc_25_chunk01.md`](../../../../../../history/extraction_audit/item_comparison/doc_25_chunk01.md)
- [`doc_25_chunk02.md`](../../../../../../history/extraction_audit/item_comparison/doc_25_chunk02.md)
- [`doc_25_chunk03.md`](../../../../../../history/extraction_audit/item_comparison/doc_25_chunk03.md)
- [`doc_26_chunk00.md`](../../../../../../history/extraction_audit/item_comparison/doc_26_chunk00.md)
- [Extraction review summary](../../../../../../history/extraction_audit/item_comparison/extraction_review_summary.md)
## Unresolved

- This artifact has **no** append-only review decision yet.
- It cannot be an evaluable downstream parent until `accepted` with a truthful decision origin.
