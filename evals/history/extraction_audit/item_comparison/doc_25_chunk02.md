# Item comparison — `doc_25_chunk02`

_Diagnostic render from existing targeted-chunk replay artifacts. No new model calls. Chunk-local facts are the trustworthy retained row for this replay. Legacy-cache rows are matched by value_text (not fact id) because the 77-fact cache is `legacy_untraceable` and ids collide across runs._

- source: `doc_25` · IEP — Fairhaven initial (4th grade)
- source_date: `2019-05-29`
- chunk: `2` / `4`
- chunk_sha256: `2dde18755f5fbdc5fb477f347fa61fb74aae1a302fca6438862ee01039a5eb88`
- model: `gpt-4o-mini` · origin: `targeted_chunk_replay`
- raw items: **7**

## Legend

| Stage | Meaning |
|---|---|
| Complete source chunk | Full chunk text for **omission / recall** review |
| Source passage | Local excerpt around one model-produced item |
| Raw extraction | Model draft before `_draft_is_skippable` |
| Transformation / drop | Deterministic disposition in this replay |
| Chunk-local fact | Fact after normalize/`draft_to_fact` in this chunk |
| Legacy ledger fact | Same-content row in the 77-fact cache, if found |
| Human item review | Append-only judgments; latest shown, history kept |

## Complete source chunk (omission surface)

_This is the full retained source for `chunk_sha256=2dde18755f5fbdc5fb477f347fa61fb74aae1a302fca6438862ee01039a5eb88`. Use it to identify evidence the model never extracted. Item-local excerpts below cannot expose omissions on their own._

**chunk_sha256:** `2dde18755f5fbdc5fb477f347fa61fb74aae1a302fca6438862ee01039a5eb88`

```text
Student Name: Emma Rose Callahan                                     Birthdate: 3/22/10                       IEP Date: 5/29/2019

Area of Need: Writing                        Measurable Annual Goal #: 2

Goal: By 5/28/2020, when given supports (graphic organizer, word bank containing transitional
Baseline: When given a prompt and asked words/phrases) Emma Rose Callahan will write an opinion piece where she introduces the topic, states her opinion
to write a paragraph, Emma Rose Callahan can formulate a clearly, supports her opinion using facts/details from the text, and provides some sense of closure
written response that contains fragmented related to her opinion with no more than 4 errors in 4 out of 5 opportunities as measured by student
or run-on sentences with errors including   work samples/teacher charted data.
inappropriate subject/verb agreement,
capitalization, proper punctuation, and         Enables student to be involved/progress in general curriculum/state standard W.4.1
spelling.
                                                 Addresses other educational needs resulting from the disability

Linguistically appropriate

Transition Goal:     Education/Training     Employment      Independent Living
                                              Person(s) Responsible: General Education and Special Education Staff
Short-Term Objective: By 11/01/2019, when given supports (graphic organizer, word bank containing transitional words/phrases) Emma Rose Callahan will write an
opinion piece where she introduces the topic, states her opinion clearly, supports her opinion using facts/details from the text, and provides some
sense of closure related to her opinion with no more than 8 errors in 2 out of 5 opportunities as measured by student work samples/teacher charted
data.

Short-Term Objective: By 3/01/2020, when given supports (graphic organizer, word bank containing transitional words/phrases) Emma Rose Callahan will write an
opinion piece where she introduces the topic, states her opinion clearly, supports her opinion using facts/details from the text, and provides some
sense of closure related to her opinion with no more than 6 errors in 3 out of 5 opportunities as measured by student work samples/teacher charted
data.

Short-Term Objective:

Progress Report 1: 11/1/2019
Summary of Progress: When given supports (graphic organizer, word bank containing transitional words/phrases) Emma Rose Callahan will write an opinion piece
where she introduces the topic, states her opinion clearly, supports her opinion using facts/details from the text, and provides some sense of closure
related to her opinion with no more than 8 errors in 2 out of 5 opportunities as measured by student work samples/teacher charted data.
Comment: Emma Rose Callahan has met the short term objective for this goal.

Progress Report 2:
Summary of Progress: When given supports (graphic organizer, word bank containing transitional words/phrases) Emma Rose Callahan will write an opinion piece
where she introduces the topic, states her opinion clearly, supports her opinion using facts/details from the text, and provides some sense of closure
related to her opinion with no more than 6 errors in 3 out of 5 opportunities as measured by student work samples/teacher charted data.
Comment: Emma Rose Callahan has me the short term objective for this goal. Great job!!

Progress Report 3:
Summary of Progress:
Comment:

Annual Review Date:
Goal met   Yes   No
Comments:
                                                                                                                               Page _____ of _____

PLACER COUNTY SELPA
                                                                          ANNUAL GOALS AND OBJECTIVES

Student Name: Emma Rose Callahan                                     Birthdate: 3/22/10                        IEP Date: 5/29/2019

Area of Need: Operations & Algebraic          Measurable Annual Goal #: 3
Thinking
                                              Goal: By 5/28/2020, given supports (graphic organizer, multiplication chart) Emma Rose Callahan will solve multi-step
                                              word problems containing whole numbers within 100 using addition, subtraction, and multiplication with
Baseline: Emma Rose Callahan can add within 100 with       80% accuracy in 4 out of 5 opportunities as measured by student work samples/teacher charted data.
93% accuracy, subtract within 100 with 83%
accuracy, and multiply within 100 with 88%       Enables student to be involved/progress in general curriculum/state standard 4.OA.A.3
accuracy. She is inconsistent when asked to
solve word problems using the 3 operations
with more than one step.                         Addresses other educational needs resulting from the disability

Linguistically appropriate

Transition Goal:   Education/Training      Employment      Independent Living
                                            Person(s) Responsible: General Education and Special Education Staff
Short-Term Objective: By 11/01/2019, given supports (graphic organizer, multiplication chart) Emma Rose Callahan will solve multi-step word problems containing
whole numbers within 100 using addition and subtraction with 80% accuracy in 4 out of 5 opportunities as measured by student work samples/teacher
charted data.

Short-Term Objective: By 3/01/2020, given supports (graphic organizer, multiplication chart) Emma Rose Callahan will solve multi-step word problems containing
whole numbers within 100 using addition, subtraction, and multiplication with 70% accuracy in 4 out of 5 opportunities as measured by student work
samples/teacher charted data.

Short-Term Objective:

Progress Report 1: 11/1/2019
Summary of Progress: Given supports (graphic organizer, multiplication chart) Emma Rose Callahan will solve multi-step word problems containing whole numbers
within 100 using addition and subtraction with 80% accuracy in 4 out of 5 opportunities as measured by student work samples/teacher charted data.
Comment: Emma Rose Callahan has met the short term objective for this goal.

Progress Report 2: 3/1/2020
Summary of Progress: Given supports (graphic organizer, multiplication chart) Emma Rose Callahan will solve multi-step word problems containing whole numbers
within 100 using addition, subtraction, and multiplication with 70% accuracy in 4 out of 5 opportunities as measured by student work samples/teacher
charted data.
Comment: Emma Rose Callahan has met the short term objective for this goal. Great job!

Progress Report 3:
Summary of Progress:
Comment:

Annual Review Date:
Goal met   Yes   No
Comments:
                                                                                                                               Page _____ of _____

PLACER COUNTY SELPA
                                                                               Offer of FAPE - SERVICE

Student Name: Emma Rose Callahan                                     Birthdate: 3/22/10                         IEP Date: 5/29/2019

The service options that were considered by the IEP team (List all): Based on the level of Emma Rose Callahan's individual needs as reflected in this IEP, the
IEP team considered a services including General Education, General Education with accommodations, and Specialized Academic Instruction support.
The IEP team concluded the least restrictive placement is a combination of General Education with accommodations and Specialized Academic
Instruction (SAI) support outside of the General Education classroom (for Language Arts and Math). SAI in the RSP setting was recommended based
on the fact that Emma Rose Callahan requires individualized, small group instruction at her current skill level to make academic progress in these core subject areas.

In selecting LRE, describe the consideration given to any potential harmful effect on the child or on the quality of services that he or
she needs: The IEP team discussed potential harmful effects including decreased access to instructional opportunities and appropriate social
interactions with typically-developing peers and the potential impact to Emma Rose Callahan's self-esteem and felt that her current needs outweigh any minimal
harmful effects at this time.
   SUPPLEMENTARY AIDS & SERVICES AND OTHER SUPPORTS FOR SCHOOL PERSONNEL, OR FOR STUDENT, OR ON BEHALF OF THE
                                                    STUDENT

The IEP team discussed and determined program accommodations are not needed in general education classes or other education-related
settings.
    The IEP team discussed and determined the following program accommodations are needed in general education classes or other education-
related settings.
 Program Accommodations                                    Start Date                End Date                     Location
 Extended Time                                             5/29/2019                 5/28/2020                    Classroom
 Preferential seating, near source of instruction and a    5/29/2019                 5/28/2020                    Classroom
 strong peer for support
 Small group setting to support assignments and tests as   5/29/2019                 5/28/2020                    Classroom
 needed
 Read out loud assessments for math and language arts      5/29/2019                 5/28/2020                    Classroom
 Graphic Organizers for math and writing assignments/tests 5/29/2019                 5/28/2020                    Classroom
 Chunk assignments/allow time for processing               5/29/2019                 5/28/2020                    Classroom

The IEP team discussed and determined program modifications are not needed in general education classes or other education-related settings.
   The IEP team discussed and determined the following program modifications are needed in general education classes or other education-related
settings.
 Program Modifications                     Start Date          End Date             Frequency           Duration             Location

The IEP team discussed and determined other supports for school personnel, or for student, or on behalf of the student are not needed.
   The IEP team discussed and determined the following other supports for school personnel, or for student, or on behalf of the student are needed.
Other Supports for School Personnel, or To Support               Start Date       End Date          Frequency        Duration        Location
for Student, or on Behalf of Student
Short-term counseling with the school       Student              5/29/2019        11/29/2019        2 times per      30 minutes      Separate
psychologist/counselor to review self-      Personnel                                               month                            Classroom
regulation strategies, coping techniques,
and check-in during transition for fourth
grade year.
```

## Recorded human coverage omissions

_None recorded yet. Use the complete source chunk above to find omissions._

## Items

## Item 00 — `doc_25:chunk:2dde18755f5f:raw:000`

### 1. Source passage (item-local excerpt)

> Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 5/29/2019 Area of Need: Writing Measurable Annual Goal #: 2 Goal: B…

### 2. Raw model extraction

- predicate: `legal_name`
- value: `Emma Rose Callahan`
- value_text: "Student Name: Emma Rose Callahan"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Student Name: Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 01 — `doc_25:chunk:2dde18755f5f:raw:001`

### 1. Source passage (item-local excerpt)

> Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 5/29/2019 Area of Need: Writing Measurable Annual Goal #: 2 Goal: By 5/28/2020, when given supports (graphic organizer, wo…

### 2. Raw model extraction

- predicate: `dob`
- value: `2010-03-22`
- value_text: "Birthdate: 3/22/10"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_002` · predicate=`dob` · value=`2010-03-22` · value_text="Birthdate: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 02 — `doc_25:chunk:2dde18755f5f:raw:002`

### 1. Source passage (item-local excerpt)

> ⚠️ **Passage not located in the full chunk text.**
>
> Needle: "4th grade"
>
> This is a human-review question — not an automatic hallucination label. Resolve against the complete source chunk above before deciding.

### 2. Raw model extraction

- predicate: `grade`
- value: `4`
- value_text: "4th grade"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_003` · predicate=`grade` · value=`4` · value_text="4th grade" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 03 — `doc_25:chunk:2dde18755f5f:raw:003`

### 1. Source passage (item-local excerpt)

> Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 5/29/2019 Area of Need: Writing Measurable Annual Goal #: 2 Goal: By 5/28/2020, when given supports (graphic organizer, word bank containing transitional Baseline:…

### 2. Raw model extraction

- predicate: `iep_status`
- value: `in place`
- value_text: "IEP Date: 5/29/2019"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'in place'}` → `{'value': 'active'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_004` · predicate=`iep_status` · value=`active` · value_text="IEP Date: 5/29/2019" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 04 — `doc_25:chunk:2dde18755f5f:raw:004`

### 1. Source passage (item-local excerpt)

> …eeds as reflected in this IEP, the IEP team considered a services including General Education, General Education with accommodations, and Specialized Academic Instruction support. The IEP team concluded the least restrictive placement is a combination of General Education with accommodations and Specialized Academic Instruction (SAI) support outside of the General Education classroom (for Language Arts and Math). SAI in the RSP setting was recommended based on the fact that Emma Rose Callahan requires individualized, small group instruction at her current skil…

### 2. Raw model extraction

- predicate: `intervention_tier`
- value: `General Education with accommodations and Specialized Academic Instruction`
- value_text: "the IEP team concluded the least restrictive placement is a combination of General Education with accommodations and Specialized Academic Instruction (SAI) support outside of the General Education classroom"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'General Education with accommodations and Specialized Academic Instruction'}` → `{'value': 'general education with accommodations and specialized academic instruction'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_005` · predicate=`intervention_tier` · value=`general education with accommodations and specialized academic instruction` · value_text="the IEP team concluded the least restrictive placement is a combination of General Education with accommodations and Specialized Academic Instruction (SAI) support outside of the General Education classroom" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 05 — `doc_25:chunk:2dde18755f5f:raw:005`

### 1. Source passage (item-local excerpt)

> …s in these core subject areas. In selecting LRE, describe the consideration given to any potential harmful effect on the child or on the quality of services that he or she needs: The IEP team discussed potential harmful effects including decreased access to instructional opportunities and appropriate social interactions with typically-developing peers and the potential impact to Emma Rose Callahan's self-esteem and felt that her current needs outweigh any minimal harmful effects at this time. SUPPLEMENTARY AIDS & SERVICES AN…

### 2. Raw model extraction

- predicate: `attendance`
- value: `regular`
- value_text: "The IEP team discussed potential harmful effects including decreased access to instructional opportunities and appropriate social interactions with typically-developing peers"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **observed silent drop** (`observed_silent_drop`)
- gate/check: `_draft_is_skippable`
- reason: `spurious_attendance`
- before→after value: `{'value': 'regular'}` → `None`

### 4. Ledger / retained fact

- chunk-local: _none_
- legacy cache (no_legacy_match): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 06 — `doc_25:chunk:2dde18755f5f:raw:006`

### 1. Source passage (item-local excerpt)

> ⚠️ **Passage not located in the full chunk text.**
>
> Needle: "to review self-regulation strategies, coping techniques, and check-in during transition for fourth grade year"
>
> This is a human-review question — not an automatic hallucination label. Resolve against the complete source chunk above before deciding.

### 2. Raw model extraction

- predicate: `behavioral_concern`
- value: `self-regulation strategies`
- value_text: "to review self-regulation strategies, coping techniques, and check-in during transition for fourth grade year"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_006` · predicate=`behavioral_concern` · value=`self-regulation strategies` · value_text="to review self-regulation strategies, coping techniques, and check-in during transition for fourth grade year" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._
