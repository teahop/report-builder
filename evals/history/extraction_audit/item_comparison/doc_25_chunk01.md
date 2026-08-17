# Item comparison — `doc_25_chunk01`

_Diagnostic render from existing targeted-chunk replay artifacts. No new model calls. Chunk-local facts are the trustworthy retained row for this replay. Legacy-cache rows are matched by value_text (not fact id) because the 77-fact cache is `legacy_untraceable` and ids collide across runs._

- source: `doc_25` · IEP — Fairhaven initial (4th grade)
- source_date: `2019-05-29`
- chunk: `1` / `4`
- chunk_sha256: `feafb23c57fb0c6522b762bb022c512ae149685cf01d079f80844fd0061c3e85`
- model: `gpt-4o-mini` · origin: `targeted_chunk_replay`
- raw items: **10**

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

_This is the full retained source for `chunk_sha256=feafb23c57fb0c6522b762bb022c512ae149685cf01d079f80844fd0061c3e85`. Use it to identify evidence the model never extracted. Item-local excerpts below cannot expose omissions on their own._

**chunk_sha256:** `feafb23c57fb0c6522b762bb022c512ae149685cf01d079f80844fd0061c3e85`

```text
Per the Health and Developmental History questionnaire filled out by parent, mom reports that Emma Rose Callahan is strong-willed and
tenacious. She appears to have low self-esteem and maintains a positive attitude towards school even though she struggles
academically. She prefers to play with others (same age or younger); she maintains a good relationship with her sister and
a very tumultuous relationship with her brother. At times, Emma Rose Callahan can be hot/cold with her peers, but mostly positive.

Psych 5/ 2019:
BASC-3 rating scales were completed by Ms. Callahan and Mrs. Reed to obtain information on Emma Rose Callahan’s behavioral and social
emotional functioning. Parent teacher rating scales indicated shared concerns in the areas of Depression, Somatization,
and Attention problems. Mrs. Reed noted additional concerns in the areas of Withdrawal and Learning Problems. Teacher
rating scales did not indicate any areas of clinical significance among behavior composites and adaptive skills. Ms. Callahan
noted clinically significant behavior symptoms associated with aggression, conduct problems, depression, attention
problems, atypicality, and adaptive skills. However, these elevated behaviors do not appear to be pervasive to a clinically
significant degree within the school setting.

The Conner’s 3 rating scales were also distributed to parent and teacher to assess behaviors typically associated with
attention deficits. Rating scale results indicated that Emma Rose Callahan demonstrates clinically significant levels of inattention in both
the home and school setting. This is consistent with record review and parent/teacher reports indicating ongoing concerns
with difficulty sustaining attention, following directions, and focusing in the classroom. Parent also indicated Clinically
Significant behaviors observed in the home including learning problems, executive functioning, defiance/aggression, and
struggles with peer relations. At school, Mrs. Reed also indicates elevated concern with Learning Problems and Peer
Relations. Significant behaviors associated with Executive Functioning, Hyperactive, and Defiance/Aggression are not
observed in the school setting.

The CDI-2 was also completed by parent, teacher, and Emma Rose Callahan, to obtain additional information on depression related
behaviors and symptoms. Parent rating scales indicated Very Elevated scores of behaviors related to depression across
both Emotional and Functional composites. Mrs. Reed indicated elevated emotional behaviors associated with depression,
but did not report any associated functional problems. Overall, Emma Rose Callahan expressed elevated levels of thoughts and behaviors
associated with depression. She scored in the Very Elevated range in the areas of Functional Problems and Ineffectiveness.
Vocational
Not an area of concern, Emma Rose Callahan can follow school/classroom rules with little to no prompting.
Adaptive/Daily Living Skills
Not an area of concern, Emma Rose Callahan can maintain her personal needs daily while at school. She can independently navigate her
way around campus during the school day.
Health
4/25/19
Hearing PASSED with both ears using the Ambco 650A pure tone audiometer.
Vision PASSED with both eyes without glasses using the HOTV chart for distance and the ETDRS chart for near vision.
                                                                                                            Page _____ of _____

Emma Rose Callahan appears healthy and stated she has no concerns. She had her appendix out earlier this month (4/1/19) but she
said she isn't having any problems from that. According to the H&D completed on 4/10/19 by mom, Emma Rose Callahan has a history
of ADHD, a sensitivity to noise/touch, sleep problems, and seasonal allergies. She last saw her dentist 7/2018. She takes
1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so information
on birth is limited. She met all of her developmental milestones on time except walking at about 19 mos and talking at
about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice.

Per mom, Emma Rose Callahan is getting fitted for a CPAP machine and will be part of a sleep study over summer.
For student to receive educational benefit, goals will be written to address the following areas of need:
Reading Fluency/Comprehension, Writing, and Math Word Problems
                                                                                                                               Page _____ of _____

PLACER COUNTY SELPA
                                                                             Statewide Assessments

Student Name: Emma Rose Callahan                                      Birthdate: 3/22/10                       IEP Date: 5/29/2019

Indicate student’s participation in the California Assessment of Student Performance and Progress (CAASPP) below:

English Language Arts (Grades 3-8, & 11)

11 With testing accommodations
     SBAC with Designated Supports Embedded
     SBAC with Designated Supports Non-embedded                         Separate Setting (i.e., most beneficial time, special lighting or acoustics,
                                                                        adaptive furniture), Simplified Test Directions
     SBAC with Accommodations Embedded                                  Text To Speech, Passages *Not available for CAA
     SBAC with Accommodations Non-embedded
     SBAC with Accessibility Support (requires CDE Approval)

Math (Grades 3-8, & 11)

11 With testing accommodations
     SBAC with Designated Supports Embedded                             Text To Speech
     SBAC with Designated Supports Non-embedded                         Separate Setting (i.e., most beneficial time, special lighting or acoustics,
                                                                        adaptive furniture), Simplified Test Directions
     SBAC with Accommodations Embedded
     SBAC with Accommodations Non-embedded                              Multiplication Table (beginning in grade 4),
     SBAC with Accessibility Support (requires CDE Approval)

Science (Grades 5, 8 & High School)

90 Not to Participate (Outside Testing Group or Plan Type 20)

If student is taking Alternate Assessment the IEP team has reviewed the criteria for taking alternate assessments.
   The student will not participate in the SBAC because
   Participation in an Alternate Assessment is appropriate because

Physical Fitness Test (Grades 5, 7 & 9)
       Out of testing range
       Without Accommodations
       With Accommodations
       With Modifications (Check with PFT Office prior to use)

Other State-Wide/ District-Wide Assessment(s) Alternate Assessment(s)

Desired Results Developmental Profile (DRDP) – (Preschoolers Ages 3, 4 and 5 years)
       Adaptations Not Applicable            Sensory support                Functional positioning
       Alternative response mode             Assistive equipment or device  Visual support
       Alternative mode for written language                                Augmentative or alternative communication system

English Language Proficiency Assessments of California (ELPAC; for English Learners Only).
Please Note: Summative ELPAC will be Computer-based beginning Spring 2020. Paper-based ELPAC will continue for 'Initial ELPAC' and grades
Kindergarten through 2nd (for the Writing domain only).

Initial ELPAC
        Without Designated Supports (All domains)
        Designated Supports (All domains)
                                                                                   Page _____ of _____

Without Accommodations (All domains)
     Accommodations (All domains)

Summative ELPAC Computer-based
   Without Designated Supports (All domains)
   Embedded Designated Supports
     Non-embedded Designated Supports
     Without Accommodations (All domains)
     Embedded Accommodations
     Non-embedded Accommodations

Alternate Assessment to ELPAC
If yes, areas of alternate assessment:   Listening  Speaking   Reading   Writing
Name of alternate assessment(s)
Person responsible to administer alternate assessment(s)

Standards based Tests in Spanish STS
    Math without Designated Supports or Accommodations
    Math with Designated Supports
    Math with Accommodations
    Reading, Language, Spelling without Designated Supports or Accommodations
    Reading, Language, Spelling with Designated Supports
    Reading, Language, Spelling with Accommodations
                                                                                                                            Page _____ of _____

PLACER COUNTY SELPA
                                                                        ANNUAL GOALS AND OBJECTIVES

Student Name: Emma Rose Callahan                                    Birthdate: 3/22/10                       IEP Date: 5/29/2019

Area of Need: Reading                        Measurable Annual Goal #: 1

Goal: By 5/28/2020, when given a text at her instructional level, Emma Rose Callahan will read the text at 104 correct
Baseline: Emma Rose Callahan can read grade level text words per minute and use context clues or draw inferences from the text in order to answer questions
at 52 CWPM and answer corresponding       with 80% accuracy in 4 out of 5 opportunities as measured by student work samples/teacher charted
comprehension questions with 71%          data.
accuracy.
                                              Enables student to be involved/progress in general curriculum/state standard RI.4.1

Addresses other educational needs resulting from the disability

Linguistically appropriate

Transition Goal:   Education/Training    Employment       Independent Living
                                              Person(s) Responsible: General Education and Special Education Staff
Short-Term Objective: By 11/01/2019, when given a text at her instructional level, Emma Rose Callahan will read the text at 70 correct words per minute and use
context clues or draw inferences from the text in order to answer questions with 70% accuracy in 4 out of 5 opportunities as measured by student work
samples/teacher charted data.

Short-Term Objective: By 3/01/2020, when given a text at her instructional level, Emma Rose Callahan will read the text at 85 correct words per minute and use
context clues or draw inferences from the text in order to answer questions with 75% accuracy in 4 out of 5 opportunities as measured by student work
samples/teacher charted data.

Short-Term Objective:

Progress Report 1: 11/1/2019
Summary of Progress: When given a text at her instructional level, Emma Rose Callahan will read the text at 70 correct words per minute and use context clues or
draw inferences from the text in order to answer questions with 70% accuracy in 4 out of 5 opportunities as measured by student work
samples/teacher charted data.
Comment: Emma Rose Callahan has met the short term objective for this goal dated 11/1/2019.

Progress Report 2: 3/1/2020
Summary of Progress: When given a text at her instructional level, Emma Rose Callahan can read the text at 85 correct words per minute and use context clues or
draw inferences from the text in order to answer questions with 75% accuracy in 4 out of 5 opportunities as measured by student work
samples/teacher charted data.
Comment: Emma Rose Callahan has met the short term objective for this goal. Great job Emma Rose Callahan!
Progress Report 3:
Summary of Progress:
Comment:

Annual Review Date:
Goal met   Yes   No
Comments:
                                                                                                                              Page _____ of _____

PLACER COUNTY SELPA
                                                                         ANNUAL GOALS AND OBJECTIVES
```

## Recorded human coverage omissions

_None recorded yet. Use the complete source chunk above to find omissions._

## Items

## Item 00 — `doc_25:chunk:feafb23c57fb:raw:000`

### 1. Source passage (item-local excerpt)

> Per the Health and Developmental History questionnaire filled out by parent, mom reports that Emma Rose Callahan is strong-willed and tenacious. She appears to have low self-esteem and maintains a positive attitude towards school even though she struggles academically. She prefers to play wi…

### 2. Raw model extraction

- predicate: `legal_name`
- value: `Emma Rose Callahan`
- value_text: "Emma Rose Callahan"
- assertion: `asserted` · reporter: `None`
- life_stage: `school-age` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Student Legal Name: Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 01 — `doc_25:chunk:feafb23c57fb:raw:001`

### 1. Source passage (item-local excerpt)

> …NTY SELPA Statewide Assessments Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 5/29/2019 Indicate student’s participation in the California Assessment of Student Performance and Progress (CAASPP) below: English Language Arts…

### 2. Raw model extraction

- predicate: `dob`
- value: `2010-03-22`
- value_text: "Birthdate: 3/22/10"
- assertion: `asserted` · reporter: `None`
- life_stage: `birth` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_002` · predicate=`dob` · value=`2010-03-22` · value_text="Birthdate: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 02 — `doc_25:chunk:feafb23c57fb:raw:002`

### 1. Source passage (item-local excerpt)

> …dentist 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so information on birth is limited. She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Per mom, Emma Rose Callahan is getting fitted for a CPAP machine and will be part of a sle…

### 2. Raw model extraction

- predicate: `developmental_history`
- value: `met all developmental milestones on time except walking at about 19 mos and talking at about 2 yrs`
- value_text: "met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs"
- assertion: `asserted` · reporter: `None`
- life_stage: `infancy` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_003` · predicate=`developmental_history` · value=`met all developmental milestones on time except walking at about 19 mos and talking at about 2 yrs` · value_text="met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_008` · predicate=`developmental_history` · value=`typical` · value_text="met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 03 — `doc_25:chunk:feafb23c57fb:raw:003`

### 1. Source passage (item-local excerpt)

> ⚠️ **Passage not located in the full chunk text.**
>
> Needle: "Emma Rose Callahan takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night"
>
> This is a human-review question — not an automatic hallucination label. Resolve against the complete source chunk above before deciding.

### 2. Raw model extraction

- predicate: `health_plan_status`
- value: `active`
- value_text: "Emma Rose Callahan takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_004` · predicate=`health_plan_status` · value=`active` · value_text="Emma Rose Callahan takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 04 — `doc_25:chunk:feafb23c57fb:raw:004`

### 1. Source passage (item-local excerpt)

> …d she has no concerns. She had her appendix out earlier this month (4/1/19) but she said she isn't having any problems from that. According to the H&D completed on 4/10/19 by mom, Emma Rose Callahan has a history of ADHD, a sensitivity to noise/touch, sleep problems, and seasonal allergies. She last saw her dentist 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of…

### 2. Raw model extraction

- predicate: `allergy_status`
- value: `known`
- value_text: "Emma Rose Callahan has a history of seasonal allergies"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_005` · predicate=`allergy_status` · value=`known` · value_text="Emma Rose Callahan has a history of seasonal allergies" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_011` · predicate=`allergy_status` · value=`known` · value_text="Emma Rose Callahan has a history of seasonal allergies" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 05 — `doc_25:chunk:feafb23c57fb:raw:005`

### 1. Source passage (item-local excerpt)

> …Callahan demonstrates clinically significant levels of inattention in both the home and school setting. This is consistent with record review and parent/teacher reports indicating ongoing concerns with difficulty sustaining attention, following directions, and focusing in the classroom. Parent also indicated Clinically Significant behaviors observed in the home including learning problems, executive functioning, defiance/aggression, and struggles with peer relat…

### 2. Raw model extraction

- predicate: `behavioral_concern`
- value: `ongoing concerns with difficulty sustaining attention, following directions, and focusing in the classroom`
- value_text: "ongoing concerns with difficulty sustaining attention, following directions, and focusing in the classroom"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `concern`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_006` · predicate=`behavioral_concern` · value=`ongoing concerns with difficulty sustaining attention, following directions, and focusing in the classroom` · value_text="ongoing concerns with difficulty sustaining attention, following directions, and focusing in the classroom" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_013` · predicate=`behavioral_concern` · value=`learning problems` · value_text="ongoing concerns with difficulty sustaining attention, following directions, and focusing in the classroom" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 06 — `doc_25:chunk:feafb23c57fb:raw:006`

### 1. Source passage (item-local excerpt)

> …rating scales were also distributed to parent and teacher to assess behaviors typically associated with attention deficits. Rating scale results indicated that Emma Rose Callahan demonstrates clinically significant levels of inattention in both the home and school setting. This is consistent with record review and parent/teacher reports indicating ongoing concerns with difficulty sustaining attention, following directions, and focusing in the class…

### 2. Raw model extraction

- predicate: `testing_impression`
- value: `demonstrates clinically significant levels of inattention in both the home and school setting`
- value_text: "demonstrates clinically significant levels of inattention in both the home and school setting"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `concern`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_007` · predicate=`testing_impression` · value=`demonstrates clinically significant levels of inattention in both the home and school setting` · value_text="demonstrates clinically significant levels of inattention in both the home and school setting" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_012` · predicate=`behavioral_concern` · value=`inattention` · value_text="demonstrates clinically significant levels of inattention in both the home and school setting" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 07 — `doc_25:chunk:feafb23c57fb:raw:007`

### 1. Source passage (item-local excerpt)

> …ntal milestones on time except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Per mom, Emma Rose Callahan is getting fitted for a CPAP machine and will be part of a sleep study over summer. For student to receive educational benefit, goals will be written to address the following areas of need: Reading Fluency/Comprehension, Writing, and Math Word Problems…

### 2. Raw model extraction

- predicate: `sleep`
- value: `getting fitted for a CPAP machine and will be part of a sleep study over summer`
- value_text: "Emma Rose Callahan is getting fitted for a CPAP machine and will be part of a sleep study over summer"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `concern`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'getting fitted for a CPAP machine and will be part of a sleep study over summer'}` → `{'value': 'getting fitted for a cpap machine and will be part of a sleep study over summer'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_008` · predicate=`sleep` · value=`getting fitted for a cpap machine and will be part of a sleep study over summer` · value_text="Emma Rose Callahan is getting fitted for a CPAP machine and will be part of a sleep study over summer" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 08 — `doc_25:chunk:feafb23c57fb:raw:008`

### 1. Source passage (item-local excerpt)

> …houghts and behaviors associated with depression. She scored in the Very Elevated range in the areas of Functional Problems and Ineffectiveness. Vocational Not an area of concern, Emma Rose Callahan can follow school/classroom rules with little to no prompting. Adaptive/Daily Living Skills Not an area of concern, Emma Rose Callahan can maintain her personal needs daily while at school. She can independently navigate her way around campu…

### 2. Raw model extraction

- predicate: `attendance`
- value: `regular`
- value_text: "Emma Rose Callahan can follow school/classroom rules with little to no prompting"
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

## Item 09 — `doc_25:chunk:feafb23c57fb:raw:009`

### 1. Source passage (item-local excerpt)

> …unusually loud voice. Per mom, Emma Rose Callahan is getting fitted for a CPAP machine and will be part of a sleep study over summer. For student to receive educational benefit, goals will be written to address the following areas of need: Reading Fluency/Comprehension, Writing, and Math Word Problems Page _____ of _____ PLACER COUNTY SELPA…

### 2. Raw model extraction

- predicate: `intervention_tier`
- value: `goals will be written to address Reading Fluency/Comprehension, Writing, and Math Word Problems`
- value_text: "goals will be written to address the following areas of need: Reading Fluency/Comprehension, Writing, and Math Word Problems"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'goals will be written to address Reading Fluency/Comprehension, Writing, and Math Word Problems'}` → `{'value': 'goals will be written to address reading fluency/comprehension, writing, and math word problems'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_009` · predicate=`intervention_tier` · value=`goals will be written to address reading fluency/comprehension, writing, and math word problems` · value_text="goals will be written to address the following areas of need: Reading Fluency/Comprehension, Writing, and Math Word Problems" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (no_legacy_match): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._
