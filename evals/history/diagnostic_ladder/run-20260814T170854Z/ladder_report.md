DIAGNOSTIC ONLY — UPSTREAM EXTRACTION/LEDGER NOT ACCEPTED

# Diagnostic ladder report — writer stage

**Run:** `run-20260814T170854Z`
**Model:** gpt-4o-mini · temperature 1.0
**Writer calls:** 4 (one per populated section; no retries)
**Tokens:** 19736 (prompt 18141 / completion 1595)
**Cost USD:** 0.003678
**Latency:** 30903 ms
**trace_alignment_status:** `not_run_diagnostic`
**Cached ledger sha256:** `1aa5f1b180002983aaf15fa797f7bce9faf159456291e0f00a8b1fe1953df7db`

| Stage | What this run can establish | Current status |
|---|---|---|
| source → raw extraction | already reviewed on the seven-item slice | known failures; not rerun |
| raw extraction → deterministic disposition | drops are visible | correct rejection can still lose useful evidence |
| disposition → ledger | exact cached parent identifiable | provisional / not accepted |
| ledger → brief | section/block routing and omissions inspectable | four compiled briefs hashed in manifest; writer received a concise subset (no fact_id/timeline/fewshot dump) |
| brief → prose | intended short prompt + full example can compose a coherent section | 4 writer calls; labeled blocks; no DOB/age opener on Current Status |
| prose → trace alignment | not exercised in this task | `not_run_diagnostic` |
| chart composition | not exercised in this task | queued independent lane; School History position marked |

## What to evaluate (separate; not one score)

1. **Server-owned order.** All four populated sections emitted. Current Status: Family History → Birth and Developmental → Health History. Educational: School History (marker) → School Experience → Intervention → IEP. Previous Evaluations: one narrative block. Rater input: student, then `Mom`, then `mother`. No empty evidence-supported prose block.

2. **Full Molly example visible.** Yes. Assistant turn is the complete Phase 1 section (A=003 Caleb, B=005 Diego, C=006 Mason, D=004 Sydney). Tests lock that the example is not buried in the case JSON.

3. **Concise brief.** Yes. Case user JSON is section plan + one narrative item per fact + attribution/dates. No `facts_by_block` / episodes / timelines / fewshots / DOB.

4. **Closer to the example than the failed long-policy smoke.** Yes on task shape: labeled thematic paragraphs, table position left to the server, no DOB/age opener, no `fact_id` authoring. Density is still thinner than Molly's examples, and Previous Evaluations still uses concessive framing ("Despite these challenges").

5. **Invented / overreached claims — flag, do not repair.** Family History was offered only `f_doc_26_008` but the prose also states RAD, ADHD, and adoption at 19 months (those ids were offered to other blocks in the same section call). Birth/dev editorializes that milestone timing "aligns with" RAD/ADHD. Health "proactive approach" / "carefully discussed and deemed necessary" is characterization. Do not retune from this.

6. **Inherited vs writer.** Inherited: unaccepted ledger; `Mom` vs `mother` split; schema gaps (social_history / nurse / COVID); chart not composed. Writer: cross-block bleed inside a section, concessive register in prior-eval, some evaluative glue sentences.

7. **Next narrow rung after Bastion.** An **accepted ledger/brief parent**. Then chart composer, then trace alignment. The writer task shape (short prompt + real example pair + prose-only schema) is reusable; do not add prompt rules from this draft.

HARD STOP. No retune. No sweep. No extraction call.
