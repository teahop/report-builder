# Extraction review summary

_Rebuildable. Anchored to diagnostic artifact hashes. Not a pass rate._

- artifact: `art_extract_audit_replay_v2`
- artifact SHA-256: `f1d7e977d46f21fc8ec11d3058e390ff6a1cff49a603af2c071d77458e65fdf3`
- run: `extract-audit-replay-20260810T231331Z-6b58509e`
- raw items: **70**
- **human-reviewed items: 7 of 70**
- human-recorded omissions: **2**
- human-unreviewed items: **63**

### Not content-review progress

- invalidated test/demo item rows (preserved in log): **9**
- invalidated test/demo coverage rows: **2**
- active synthetic item rows (should be 0 on the live run): **0**
- active synthetic coverage rows (should be 0 on the live run): **0**

## Chunk hashes

- `doc_11_chunk01`: `9a3d5d2298aafea9b00722226387d629b5fe5ba0c0ccedfa54bd2182d86aaaf6`
- `doc_11_chunk02`: `fc9b786c086bdcbda3db99e1df0281969642c2d49223d8e33a2d534484db7189`
- `doc_11_chunk04`: `6fa5cd841ec5ccd0dd3fdab6a44eb1848eb0ed619fcbc17200d51a86e2438c8a`
- `doc_25_chunk00`: `a78ed6a8ceb761b4177007668ab1843da6985615a83b9499209bd2db4fa60d59`
- `doc_25_chunk01`: `feafb23c57fb0c6522b762bb022c512ae149685cf01d079f80844fd0061c3e85`
- `doc_25_chunk02`: `2dde18755f5fbdc5fb477f347fa61fb74aae1a302fca6438862ee01039a5eb88`
- `doc_25_chunk03`: `c70e8192a71c6521965d635cead1227d3b56bd2e8e7cfdcf7cd0474b3273c25a`
- `doc_26_chunk00`: `481263420851271c4102f6d218e7c2311e59959081c3d886b2dcbc926518e658`

## Counts by review dimension (latest **human** judgment per item)

| Dimension | pass | fail | uncertain | not_applicable |
|---|---:|---:|---:|---:|
| `source_support` | 5 | 2 | 0 | 0 |
| `predicate` | 3 | 3 | 1 | 0 |
| `value` | 3 | 2 | 2 | 0 |
| `metadata` | 7 | 0 | 0 | 0 |
| `deterministic_disposition` | 3 | 1 | 3 | 0 |

## Observed silent drops

- `doc_11:chunk:fc9b786c086b:raw:002`
- `doc_11:chunk:6fa5cd841ec5:raw:002`
- `doc_11:chunk:6fa5cd841ec5:raw:004`
- `doc_25:chunk:feafb23c57fb:raw:008`
- `doc_25:chunk:2dde18755f5f:raw:005`
- `doc_26:chunk:481263420851:raw:002`

## Retained/transformed items with human fail/uncertain source_support, predicate, or value

- `doc_11:chunk:6fa5cd841ec5:raw:005` · chunk=`6fa5cd841ec5…` · {'predicate': 'fail', 'value': 'fail'} · tj/human — Provisionally retain as contextualized written-expression performance; Molly should confirm the clinical categorization. basic_reading with value 5 is not an acceptable representation.
- `doc_11:chunk:6fa5cd841ec5:raw:006` · chunk=`6fa5cd841ec5…` · {'predicate': 'uncertain', 'value': 'uncertain'} · tj/human — The evidence belongs in Educational History. Preserve the full math-performance context rather than only the unexplained scalar 90; exact predicate remains open.

## Human-recorded omissions by chunk

### Chunk `6fa5cd841ec5…`

- Written-expression baseline, goal, and progress were not emitted as correctly typed, contextualized facts. · locator="Area of Need: Written Expression" · proposed_predicate=`written_expression` (provisional) · tj/human
- Math baseline and classroom-strength evidence were omitted as clean Educational History facts. · locator="skills and good algebraic thinking" · tj/human


## Human-unreviewed raw items

_63 items still without a human judgment (list truncated to 20):_

- `doc_11:chunk:9a3d5d2298aa:raw:000`
- `doc_11:chunk:9a3d5d2298aa:raw:001`
- `doc_11:chunk:9a3d5d2298aa:raw:002`
- `doc_11:chunk:9a3d5d2298aa:raw:003`
- `doc_11:chunk:9a3d5d2298aa:raw:004`
- `doc_11:chunk:9a3d5d2298aa:raw:005`
- `doc_11:chunk:9a3d5d2298aa:raw:006`
- `doc_11:chunk:fc9b786c086b:raw:000`
- `doc_11:chunk:fc9b786c086b:raw:001`
- `doc_11:chunk:fc9b786c086b:raw:002`
- `doc_11:chunk:fc9b786c086b:raw:003`
- `doc_11:chunk:fc9b786c086b:raw:004`
- `doc_11:chunk:fc9b786c086b:raw:005`
- `doc_11:chunk:fc9b786c086b:raw:006`
- `doc_11:chunk:fc9b786c086b:raw:007`
- `doc_11:chunk:fc9b786c086b:raw:008`
- `doc_11:chunk:fc9b786c086b:raw:009`
- `doc_11:chunk:fc9b786c086b:raw:010`
- `doc_11:chunk:fc9b786c086b:raw:011`
- `doc_25:chunk:a78ed6a8ceb7:raw:000`
- … +43 more

## Log integrity

- item review log rows for this artifact SHA (including invalidated): **16**
- coverage omission log rows (including invalidated): **4**

_Artifact acceptance remains a separate human decision after review._
