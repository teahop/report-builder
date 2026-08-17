# Stage receipts (eval-only)

Immutable, content-hashed stage receipts for reviewable pipeline evaluation.
Independent of Langfuse and the production provider. **No model calls.**

Receipt **v2**: mutable review status and stage evals live in append-only
`decisions.jsonl` / `evals.jsonl`. Immutable **evidence views** never include
review status. Rebuildable **current review views** are regenerated when a
decision or eval is appended.

## Layout

```text
evals/receipts/
  hashing.py models.py store.py review.py stage_evals.py validate.py render.py
  index_extraction_audit.py
  build_synthetic_chain.py
  store/
    by_sha/                         # content-addressed machine + evidence
    runs/<run_id>/
      receipts/                     # immutable
      decisions.jsonl               # append-only
      evals.jsonl                   # append-only
      index.md                      # rebuildable
      review_views/current/*.md     # rebuildable — open these for review
      evidence_views/*.md           # named pointers to immutable evidence
```

## Dev / test dependency

Production `requirements.txt` does **not** include pytest. For the focused suite:

```bash
cd week-1
python -m venv .venv && source .venv/bin/activate   # or use existing .venv
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest test_stage_receipts.py -q
```

## Commands

```bash
.venv/bin/python -m evals.receipts.index_extraction_audit
.venv/bin/python -m evals.receipts.build_synthetic_chain
.venv/bin/python -m evals.receipts.review record \
  --run <run_id> --artifact <artifact_id> --decision accepted \
  --origin human --reviewer-id <id> --reviewer-role engineer --notes "…"
.venv/bin/python -m evals.receipts.stage_evals \
  --run <run_id> --artifact <id> --check-id foo --check-version 1 --result pass
```

## Decision origin

| Origin | Identity |
|---|---|
| `human` | Real reviewer id after actual review (or explicit delegation) |
| `synthetic_test` | Must be `receipt_test_harness` / `automated_test` |

Automation must never emit `tj`, `molly`, or other human ids.

## Dispositions

Evaluable lineage forbids `observed_silent_drop`. That kind is diagnostic-only
and means the historical code path **silently omitted** the item (not quarantined).

## Lineage

| Kind | Meaning |
|---|---|
| `evaluable` | May become an accepted parent after truthful review |
| `diagnostic_replay` | Replay/audit evidence |
| `legacy_untraceable` | Pre-receipt artifact outside the evaluable chain |
| `non_evaluable_preview` | Explicit preview; not accepted |

The targeted extraction audit is **not** the parent of `evals/cache/fixture_001_ledger.json`.
