# History extraction-call audit (diagnostic only)

**Status:** diagnostic complete — no prompt/gate/selector/brief/writing repairs in this pass  
**Origin:** `targeted_chunk_replay` (not original 2026-08-10 full-fixture Langfuse generations)  
**Model:** `gpt-4o-mini` · temperature `0.0` (same as production extract)  
**Runner:** `evals/history/audit_extraction_chunks.py`  
**Fixture ledger compared:** `evals/cache/fixture_001_ledger.json` (built 2026-08-10T21:52:19Z, then gate-filtered)

## How this was run

1. Used normal `split_source_content` (12k char limit) on `fixtures/fixture_001` sources.
2. Selected only chunks containing the audit passages (plus controls in those chunks).
3. Langfuse export was **not** available in this pass (`EXTRACTION_AUDIT_LANGFUSE_DIR` unset; no original generation recovery). Results are a **replay**.
4. For each chunk: captured parsed `SourceExtraction.facts` **before** `_draft_is_skippable`, then traced skip reason → normalize/`draft_to_fact` → dedupe → medication consolidation.
5. Compared matched raw drafts to the surviving final-ledger rows for the named fact ids.

### Call count and cost

| Wave | Chunks called | Prompt tokens | Completion tokens | Est. USD |
|---|---:|---:|---:|---:|
| First replay | 7 | (see per-chunk JSON) | | ~0.0128 |
| Missing `doc_11` chunk 4 | 1 | 9460 total that call | | ~0.0017 |
| **Total new extraction calls** | **8** | **~76.4k cumulative** | | **~$0.0145** |

System prompt SHA (current tree): see `audit_summary.json` → `run.system_prompt_sha256`.  
Per-chunk user-payload SHA and chunk SHA: each `*_chunkNN.json`.

### Artifacts

| Path | Contents |
|---|---|
| `audit_summary.json` | Run metadata + claim→raw/post/final matches |
| `doc_11_chunk01.json` | Adaptive/impede passage chunk |
| `doc_11_chunk02.json` | RAD/ADHD + medication control |
| `doc_11_chunk04.json` | Paragraph / 5th-grade writing passage |
| `doc_25_chunk00.json` | IEP form “Not Eligible / Exiting” |
| `doc_25_chunk01.json` / `doc_25_chunk03.json` | Adoption + guanfacine/milestone (content repeats across chunks) |
| `doc_25_chunk02.json` | Supplementary aids / other-supports section |
| `doc_26_chunk00.json` | Trauma checklist + meds/allergies denial + sleep control |

Local artifacts may contain approved-anonymized source text. Do not paste them into tickets or external tools.

---

## Classification table

`Defect owner` is exactly one of the required labels. When this replay did not re-emit a final-ledger wrong fact, owner is `cannot_determine_from_replay` even though code inspection still says registered predicates are not retagged by post-processing.

| Claim | Source meaning | Raw model result (this replay) | Post-processing result | Final ledger result | Defect owner |
|---|---|---|---|---|---|
| Adaptive behavior ≠ reading (`f_doc_11_012`) | “Behavior is adaptive and does not impede learning” is adaptive/behavior language, not reading skill. | Emitted `behavioral_concern` (wrong topic). Not skipped. | Predicate preserved; retained. | `basic_reading` / “adaptive…does not impede learning” | `cannot_determine_from_replay` |
| RAD/ADHD ≠ trauma (`f_doc_11_014`) | Diagnosis labels alone are not a trauma narrative. | Emitted `trauma_history` value `rad and adhd`. Not skipped. | Predicate preserved; retained. | `trauma_history` / “has RAD and ADHD” | `extraction_prompt_or_vocabulary` |
| Paragraph writing ≠ reading (`f_doc_11_017`) | Writing a paragraph / supporting sentences is written expression. | Emitted `basic_reading` about paragraph/expository writing. Not skipped. | Predicate preserved; retained. | `basic_reading` / paragraph at ~5th grade | `extraction_prompt_or_vocabulary` |
| Unmarked IEP form options (`f_doc_25_006`) | Blank “Not Eligible / Exiting” options are not an active determination. | Emitted `iep_status` with `value=in place`, `value_text=` form option string, `assertion=asserted`. Existing `_is_spurious_iep_status` did **not** skip. | `normalize_value` mapped `in place` → **`active`**, amplifying the error; retained as asserted active. | `iep_status` / form option text (value `active`) | `extraction_prompt_or_vocabulary` |
| School supports ≠ medications (`f_doc_25_016`) | “Other supports…not needed” is services determination, not meds. | Passage present in `doc_25` chunk 2; **this replay emitted no draft** for that determination. | N/A (omitted). | `medications` / supports-not-needed text | `cannot_determine_from_replay` |
| Adoption ≠ trauma (`f_doc_25_019`) | “Adopted at 19 months…birth info limited” is adoption/birth-history context, not trauma. | Emitted `trauma_history`. Not skipped. | Predicate preserved; retained. | `trauma_history` / adopted at 19 months | `extraction_prompt_or_vocabulary` |
| Child trauma checklist ≠ family Hx (`f_doc_26_008`) | Checklist of suspected neglect/trauma is about the child (trauma/history of adversity), not family medical/psych history. | Passage present in `doc_26` chunk 0; **this replay emitted no draft** for the checklist line (did emit other `family_history` rows about parents’ incarceration/substance use). | N/A for the checklist claim. | `family_history` / checklist trauma/neglect text | `cannot_determine_from_replay` |
| “No meds or allergies” ≠ IHP (`f_doc_26_010`) | Denies medications and allergies; does not state individual health-plan status. | Passage present; **this replay emitted no draft** for that sentence. | N/A. | `health_plan_status` / “No medications or allergies” | `cannot_determine_from_replay` |
| **Control** milestone walk (doc_25) | Walking ~19 months / milestones. | Emitted `developmental_history` including walking/talking milestone language (also separate walked-age content in corpus). Retained. | Kept. | (ledger has related milestone rows) | `not_a_defect` |
| **Control** medications guanfacine (doc_25) | Named meds list should be `medications`. | Emitted **`health_plan_status`** for the guanfacine/Singular/melatonin sentence. Not skipped by current health-plan gates. | Predicate preserved; retained as health_plan. | (ledger also has true `medications` rows from other extracts) | `extraction_prompt_or_vocabulary` |
| **Control** sleep (doc_26) | Sleeps well 8–6:30 without snoring. | Emitted `sleep`. Retained. | Kept. | Matches sleep evidence | `not_a_defect` |
| **Control** meds Geodon/Trileptal/Vyvance (doc_11) | Named meds. | Emitted `medications`. Retained. | Kept. | Matches medication evidence | `not_a_defect` |

### Notes on owners (not alternate labels)

- For `f_doc_11_012`, replay and final ledger disagree on predicate (`behavioral_concern` vs `basic_reading`). Both are wrong relative to source meaning; without the original generation we cannot name the 2026-08-10 raw predicate. Code inspection still says post-processing does not retag registered predicates.
- For `f_doc_25_006`, extraction invented an affirmative IEP status from form boilerplate; normalize then forced `active`. Root owner remains extraction; post-processing **amplified** rather than created the wrong predicate.
- Wrong raw predicates are **not** classified as `brief_selector` failures.

---

## Required cross-cutting answers

### 1. `provisional_tj_v1` topics without a non-distorting registered predicate

From `predicates.py` / structure needs (inference from vocabulary inventory + sampled failures):

| Needed History evidence | Closest registered predicate(s) | Distortion risk |
|---|---|---|
| Medical / psychiatric **diagnoses** (RAD, ADHD, etc.) | none dedicated; falls into `trauma_history`, `behavioral_concern`, or `__unregistered__` | High — sampled as `trauma_history` |
| Adoption / custody placement timing (non-trauma) | none dedicated; falls into `trauma_history` or narrative developmental catch-alls | High — sampled as `trauma_history` |
| Broad **social history** (peers, friendships, social activities) | none (`SOCIAL_HISTORY_PREDICATES` empty in selectors; no social-* predicates) | Structure block cannot be populated without distortion or omission |
| Nurse-report identity | no `SourceType` nurse / nurse predicates | Structure gap (already recorded) |
| Child adversity / trauma **checklist** vs family medical history | `trauma_history` vs `family_history` both exist but checklist was stored as `family_history` in the final ledger | Boundary unclear to the model |
| Individual health plan vs “no meds/allergies” | `health_plan_status` vs `medications` / `allergy_status` | Sampled final ledger used IHP for a dual denial |

### 2. Did `__unregistered__` appear?

**No.** Across all 8 replayed chunks, raw drafts contained **zero** `__unregistered__` / `proposed_predicate` uses.

**Inference (not proof):** the extract prompt’s “Prefer registered predicates; use `__unregistered__` + `proposed_predicate` only when none fit” likely pressures nearest-label classification into existing names (`trauma_history`, `basic_reading`, `health_plan_status`, `family_history`) when the true concept is missing. The diagnosis and adoption failures are consistent with that pressure, but a single replay cannot prove causation.

### 3. Reporter when attribution is explicit?

In the sampled chunks, when the text said “Mom is concerned…”, the model **did** set `reporter` to `mother` / `teacher` on several `behavioral_concern` drafts (`doc_25_chunk00`).  
Many other drafts still have `reporter: null` even when a source label would be the only attribution (expected under “never invent reporter”). No clear missed *explicit* “Mother said …” pattern was found in these chunks beyond the Mom/teacher cases that were filled.

### 4. Silent discard vs quarantine?

Extract skips **drop drafts from the ledger with no review-queue object** (unlike History compiler future-date review). In this audit:

| Skipped draft | Reason | Meaningful? |
|---|---|---|
| “reading at a 7th grade reading level” as `grade` | `spurious_grade` | **Yes — silent discard.** Likely belonged on a reading predicate; gate deleted it instead of quarantining or retargeting. |
| “Math 10 class” as `grade` | `spurious_grade` | Borderline / future-track; skip likely appropriate. |
| Several attendance mistags | `spurious_attendance` | Mostly appropriate. |
| “Developmental history…exposure to trauma” as `developmental_history` | `spurious_developmental_history` | Gate correctly blocked a known wrong bag; still silent (no extract-time quarantine record). |

So: **yes**, at least one meaningful claim was silently discarded (`7th grade reading level` mistagged as `grade`).

---

## Smallest separable repair options (for TJ/Cowork — do not implement here)

One variable each:

1. **Vocabulary first:** add registered predicates (or explicit `__unregistered__` encouragement) for `diagnosis` / `adoption_history` / social-relationship topics so the model has a non-distorting home.  
2. **Prompt distinctions only:** tighten `trauma_history` vs diagnosis vs adoption; `basic_reading` vs `written_expression`; `health_plan_status` vs meds/allergies; `family_history` vs child trauma checklist — without new predicates.  
3. **Post-processing quarantine:** when skip fires on a mistagged-but-substantive draft (e.g. reading level as `grade`), emit a review item instead of deleting; fix `iep_status` normalize so `value_text` form-denial cannot become `active`.  
4. **Model/context:** re-measure the same chunks on a stronger extract model with identical prompt/vocab (isolates capability).  
5. **Only after ledger trust:** resume brief/selector work (accounting states) — not before.

Recommended order for debate: **(1) or (2) before more gates**, because several surviving wrong predicates never hit current skip filters; new regexes would chase symptoms. Use (3) for the IEP normalize amplification and silent `grade` discard. Use (4) only if (1)/(2) still fail on replay.

---

## Hard stop

No edits to `extract_prompt.md`, `predicates.py`, gates, selectors, compiler, briefs, or writing prompts. No History draft smoke. Awaiting TJ/Cowork choice of the next single variable.
