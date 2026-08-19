# Re-assign facts whose value shape does not match the predicate

The first extraction assigned one or more claims to predicates whose **declared value shapes** do not fit the values. Those claims were not dropped as evidence — they are listed in the user payload as `mismatched_drafts`.

Re-emit **each** mismatched claim exactly once:

1. Keep the claim (value / value_text / assertion / qualifier / reporter / valence / source_section / as_of_date / life_stage / grade / confidence / subject). Do not invent a new claim and do not omit one.
2. Choose a registered predicate whose declared shapes fit this value. Unlisted predicates accept free text.
3. Do not reuse the original predicate if its declared shapes still fail.
4. If no registered predicate represents the claim's domain *and* fits the value's shape, use `predicate: __unregistered__` with a `proposed_predicate`.

Return `SourceExtraction` with a `facts` list — same schema as first-pass extraction.

Do **not** write prose. Do not use outside knowledge. Match predicate to claim domain using the preferred-predicate list; the shape table only constrains which predicates may carry which value types.

## Declared value shapes

{{SHAPE_LIST}}

Unlisted predicates accept any value (free text).

## Preferred predicates

{{PREDICATE_LIST}}
