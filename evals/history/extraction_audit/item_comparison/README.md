# Extraction item comparisons

_Generated from existing audit replay artifacts — no new model calls._

- Origin: `targeted_chunk_replay`
- Not the original 2026-08-10 Langfuse generations
- Not the parent of the legacy 77-fact cache
- Extraction content remains unreviewed at the artifact level until a human records an artifact decision

**Start here** for the small 7-item slice:
- [`doc_11_chunk04.md`](doc_11_chunk04.md)

- [Extraction review summary](extraction_review_summary.md)

All chunks:

- [`doc_11_chunk01.md`](doc_11_chunk01.md) — raw=7 retained=6 transformed=1 silent_drop=0 passage_missing=0
- [`doc_11_chunk02.md`](doc_11_chunk02.md) — raw=12 retained=9 transformed=2 silent_drop=1 passage_missing=2
- [`doc_11_chunk04.md`](doc_11_chunk04.md) — raw=7 retained=5 transformed=0 silent_drop=2 passage_missing=0
- [`doc_25_chunk00.md`](doc_25_chunk00.md) — raw=10 retained=8 transformed=2 silent_drop=0 passage_missing=0
- [`doc_25_chunk01.md`](doc_25_chunk01.md) — raw=10 retained=7 transformed=2 silent_drop=1 passage_missing=1
- [`doc_25_chunk02.md`](doc_25_chunk02.md) — raw=7 retained=4 transformed=2 silent_drop=1 passage_missing=2
- [`doc_25_chunk03.md`](doc_25_chunk03.md) — raw=6 retained=5 transformed=1 silent_drop=0 passage_missing=0
- [`doc_26_chunk00.md`](doc_26_chunk00.md) — raw=11 retained=9 transformed=1 silent_drop=1 passage_missing=2

## Recording item / coverage judgments

```bash
cd week-1
.venv/bin/python -m evals.history.item_review record-item \
  --run extract-audit-replay-20260810T231331Z-6b58509e \
  --artifact art_extract_audit_replay_v2 \
  --chunk-sha <chunk_sha256> \
  --item-id '<item_id>' \
  --origin human --reviewer-id tj --reviewer-role engineer \
  --source-support pass --predicate fail --value uncertain \
  --metadata pass --deterministic-disposition pass \
  --notes '…' --refresh

.venv/bin/python -m evals.history.item_review record-omission \
  --run extract-audit-replay-20260810T231331Z-6b58509e \
  --artifact art_extract_audit_replay_v2 \
  --chunk-sha <chunk_sha256> \
  --source-locator 'exact quote or locator' \
  --description 'omitted claim' \
  --origin human --reviewer-id tj --reviewer-role engineer \
  --proposed-predicate diagnosis --refresh
```

Or regenerate surfaces after hand-editing is never required:

```bash
.venv/bin/python -m evals.history.refresh_extraction_review_surfaces
```

