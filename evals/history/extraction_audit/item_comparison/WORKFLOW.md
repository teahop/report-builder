# Recording extraction item / coverage judgments

Hand these commands to Cursor/Cowork. Do **not** edit JSON by hand.

Diagnostic run: `extract-audit-replay-20260810T231331Z-6b58509e`  
Artifact: `art_extract_audit_replay_v2`

## Item judgment

```bash
cd ai-engineering-bootcamp-v2/week-1
.venv/bin/python -m evals.history.item_review record-item \
  --run extract-audit-replay-20260810T231331Z-6b58509e \
  --artifact art_extract_audit_replay_v2 \
  --chunk-sha <chunk_sha256 from the comparison page> \
  --item-id '<item_id from the comparison page>' \
  --origin human --reviewer-id tj --reviewer-role engineer \
  --source-support pass \
  --predicate fail \
  --value uncertain \
  --metadata pass \
  --deterministic-disposition pass \
  --notes 'optional note' \
  --refresh
```

Statuses: `pass` | `fail` | `uncertain` | `not_applicable`  
Dimensions are independent — one may fail without forcing the others.

## Coverage omission

```bash
.venv/bin/python -m evals.history.item_review record-omission \
  --run extract-audit-replay-20260810T231331Z-6b58509e \
  --artifact art_extract_audit_replay_v2 \
  --chunk-sha <chunk_sha256> \
  --source-locator 'exact quote from the complete source chunk' \
  --description 'what was omitted' \
  --origin human --reviewer-id tj --reviewer-role engineer \
  --proposed-predicate diagnosis \
  --refresh
```

Proposed predicates default to **provisional**.

## Refresh surfaces only

```bash
.venv/bin/python -m evals.history.refresh_extraction_review_surfaces
```
