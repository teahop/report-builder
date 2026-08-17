# Item comparison — `doc_11_chunk04`

_Diagnostic render from existing targeted-chunk replay artifacts. No new model calls. Chunk-local facts are the trustworthy retained row for this replay. Legacy-cache rows are matched by value_text (not fact id) because the 77-fact cache is `legacy_untraceable` and ids collide across runs._

- source: `doc_11` · IEP — current school records
- source_date: `2024-10-02`
- chunk: `4` / `9`
- chunk_sha256: `6fa5cd841ec5ccd0dd3fdab6a44eb1848eb0ed619fcbc17200d51a86e2438c8a`
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

## Review prompts for this slice (not pre-decided labels)

- **item 02:** course name interpreted as grade, then dropped — is the extraction wrong, the drop appropriate, or both?
- **item 03:** annual-review date interpreted as active IEP status — supported by source?
- **item 04:** classroom-strength evidence interpreted as attendance, then dropped — what evidence was lost?
- **item 05:** writing performance interpreted as basic_reading with value `5` — predicate and value both reviewable?
- **item 06:** retained math claim whose local supporting passage was not located — resolve against the full chunk below before deciding.

## Complete source chunk (omission surface)

_This is the full retained source for `chunk_sha256=6fa5cd841ec5ccd0dd3fdab6a44eb1848eb0ed619fcbc17200d51a86e2438c8a`. Use it to identify evidence the model never extracted. Item-local excerpts below cannot expose omissions on their own._

**chunk_sha256:** `6fa5cd841ec5ccd0dd3fdab6a44eb1848eb0ed619fcbc17200d51a86e2438c8a`

```text
Area of Need: Math Problem Sovling       Measurable Annual Goal #:

Goal: By October 2, 2024, given notes and prior practice, Emma Rose Callahan will solve 5 multi-step linear
Baseline: Emma Rose Callahan has been exposed to equations with positive and negative rational number coefficients, including equations whose
one-step equations, but not multi-step solutions require expanding expressions using the distributive property and collecting like
equations. She has some strong math terms, with at least 75% accuracy in 1/2 trials, as measured by student work samples/teacher
skills and good algebraic thinking. She records. 8.EE.7b
has kept up with her GE Math instruction
so far this year. Although her GE Math       Enables student to be involved/progress in general curriculum/state standard 8.EE.7b
grade does not currently reflect it, she
understands the material (exponents,         Addresses other educational needs resulting from the disability
scientific notation and roots). While she
does not test particularly well in math,     Linguistically appropriate
she does well on practice problems in
her Math 10 class.                           Transition Goal: Education/Training Employment Independent Living
                                          Person(s) Responsible: GE Teacher, SAI Teacher, Case Manager and Student
Short-Term Objective: By December 2023 , given notes and prior practice, Emma Rose Callahan will understand the concept of a linear equation and
will solve 5 one-step equations with whole number coefficients with at least 80% accuracy in 1/2 trials as measured by student work
samples/teacher records.

Short-Term Objective: By May 2024, given notes and prior practice, Emma Rose Callahan will solve 5 two-step linear equations with rational number
coefficients with at least 80% accuracy in 1/2 trials as measured by student work samples/teacher records.

Short-Term Objective:

Progress Report 1: 12/13/2023
Summary of Progress: Given notes and prior practice, Emma Rose Callahan understands the concept of a linear equation and can solve 5 one-step
equations with whole number coefficients with at least 90% accuracy in 1/2 trials as measured by student work samples/teacher records.
She can also solve one-step equations with decimal and fraction coefficients with the same accuracy. This objective has been met.
Comment: Emma Rose Callahan's focus, productivity and accuracy have improved greatly in the past few months. Emma Rose Callahan takes her classwork seriously
and helps other students. She is a pleasure to have in class.

Progress Report 2: 5/13/2024
Summary of Progress: Given notes and prior practice, Emma Rose Callahan can solve 5 two-step linear equations with rational number coefficients
with at least 80% accuracy in 1/2 trials as measured by student work samples/teacher records. This objective has been met.
Comment: Emma Rose Callahan puts in a lot of work in her Math support class. She is polite, engaged and a joy to teach.

Progress Report 3:
Summary of Progress:
Comment:

Annual Review Date: 10/2/2024
Goal met Yes No
Comments: Per teacher feedback:9/29/24: Math 1 Foundations has not yet covered the math material listed in Emma Rose Callahan's IEP. It is actually
our next unit, which begins on Monday, September 30. So, I won't have this data for a few weeks.

Based off her prior progress report she met her gaol in May 2024. She continues to make progress based on her current grade in her
math class.
                                                                                                                  Page _____ of _____

RIDGEWAY-CORDOVA SELPA
                                                       ANNUAL GOALS AND OBJECTIVES

Student Name: Emma Rose Callahan                                Birthdate: 3/22/10                   IEP Date: 10/2/2024

Area of Need: Written Expression          Measurable Annual Goal #:

Goal: By 10/02/2024, when given a writing topic and a graphic organizer, Emma Rose Callahan will write a 2
Baseline: Emma Rose Callahan struggles to write        paragraph expository essay with an emerging topic sentence, 4-6 supporting sentences and a
coherent parapraphs with appropriate summary conclusion using appropriate grade level language and conventions with at least 80%
structure and grade level language. She accuracy in 2 of 3 trials as measured by student work samples.
can write a paragraph and supporting
sentences at an approximate 5th grade        Enables student to be involved/progress in general curriculum/state standard RL.8.1
level. She has things to say and thoughts
to get across, but doesn't take time to      Addresses other educational needs resulting from the disability
edit her work to ensure that it is
presented in a logical, coherent manner.     Linguistically appropriate

Transition Goal:    Education/Training   Employment      Independent Living
                                          Person(s) Responsible: GE Teachers, Case Manager and Student
Short-Term Objective: By December 2023, when given a writing topic and a graphic organizer, Emma Rose Callahan will write a paragraph expository
essay with an emerging topic sentence, 2-3 supporting sentences and a summary conclusion using appropriate grade level language and
conventions with at least 70% accuracy as measured by student work samples.

Short-Term Objective: By May 2024, when given a writing topic and a graphic organizer, Emma Rose Callahan will write a 2 paragraph expository
essay with an emerging topic sentence, 3-5 supporting sentences and a summary conclusion using appropriate grade level language and
conventions with at least 75% accuracy as measured by student work samples.

Short-Term Objective:

Progress Report 1: 12/10/2023
Summary of Progress: When given a writing topic and a graphic organizer, Emma Rose Callahan can write a paragraph expository essay with an
emerging topic sentence, 2-3 supporting sentences and a summary conclusion using appropriate grade level language and conventions
with at least 70% accuracy as measured by student work samples. This objective has been met.
Comment: Emma Rose Callahan is making progress toward this goal.

Progress Report 2: 5/24/2024
Summary of Progress: When given a writing topic and a graphic organizer, Emma Rose Callahan can write a 2 paragraph expository essay with an
emerging topic sentence, 3-5 supporting sentences and a summary conclusion using appropriate grade level language and conventions
with at least 75% accuracy as measured by student work samples.
Comment: Emma Rose Callahan cares about her grades and gives her best effort!

Progress Report 3:
Summary of Progress:
Comment:

Annual Review Date: 10/2/2024
Goal met Yes No
Comments: At this time Emma Rose Callahan has not written an essay in her class yet. Based on her progress report Emma Rose Callahan was shy of meeting her
goal. This will be an area in which Emma Rose Callahan will continue to work on.
                                                                                                                Page _____ of _____

RIDGEWAY-CORDOVA SELPA
                                                             SPECIAL FACTORS

Student Name: Emma Rose Callahan                               Birthdate: 3/22/10                  IEP Date: 10/2/2024

Does the student require assistive technology devices and/or services?             Yes   No

Rationale: Emma Rose Callahan does not require assistive technology to access the curriculum.

Does the student require low incidence services, equipment and/or materials to meet educational goals? Yes No
(If yes, specify) Emma Rose Callahan does not require low incidence services, equipment and/or materials to meet educational goals as she does not
have a low incidence disability.

Considerations if the student is blind or visually impaired: Emma Rose Callahan is not blind or visually impaired.

Considerations if the student is deaf or hard of hearing: Emma Rose Callahan is not deaf or hard of hearing.

If the student is an English Learner, complete the following section:
1. All students who are English Learners must receive Comprehensive English Language Development (ELD) (designated
   and Integrated ELD instruction) as part of their core instructional program, based on assessed English language
   proficiency.

a. Does the student need primary language supports during integrated ELD (across content areas)?                Yes    No

If yes, please select:
        Oral clarification of directions in the primary language
        Illustrated glossaries in primary language
        Graphic organizer with key concepts translated to primary language
        Pair key text/words translated to primary language with visuals
        Pair key text/words translated to primary language
        Provide definitions in primary language in context of lesson
        Frontloading using primary language, to bridge new learning to previous knowledge
        Teach relationships between concepts in primary language
        Conduct frequent comprehension checks, allow for student response in primary language
        Bilingual dictionary
        Glossaries in primary language
        Other:

b. Where will the student receive Designated ELD?           General Education     Special Education

2. The student who is an English Learner is currently participating in:
     Structured English Immersion (SEI) or Other, parent selected multilingual/language acquisition program
Comments:

Does student's behavior impede learning of self or others?          Yes    No (describe)

If yes, specify positive behavior interventions, strategies, and supports:

Behavior Goal is part of this IEP   Behavior Intervention Plan (BIP) Attached
                                                                                                               Page _____ of _____

RIDGEWAY-CORDOVA SELPA
                                                           Statewide Assessments

Student Name: Emma Rose Callahan                              Birthdate: 3/22/10                 IEP Date: 10/2/2024

Indicate student’s participation in the California Assessment of Student Performance and Progress (CAASPP) below:

English Language Arts (Grades 3-8, & 11)

90 Not to Par cipate (Outside Tes ng Group or Plan Type 200)

Math (Grades 3-8, & 11)

90 Not to Par cipate (Outside Tes ng Group or Plan Type 200)

Science (Grades 5, 8 & High School)

90 Not to Par cipate (Outside Tes ng Group or Plan Type 200)

If student is taking Alternate Assessment the IEP team has reviewed the criteria for taking alternate assessments.

Physical Fitness Test (Grades 5, 7 & 9)
       Out of testing range
       Without Accommodations
       With Accommodations
       With Modifications (Check with PFT Office prior to use)

Other State-Wide/ District-Wide Assessment(s) Alternate Assessment(s)

Desired Results Developmental Profile (DRDP) – (Preschool and TK Students, Ages 3-5 Years)
       Adaptations Not Applicable         Sensory support                    Functional positioning
       Alternative response mode          Assistive equipment or device      Visual support
       Alternative mode for written language                                 Augmentative or alternative communication system

English Language Proficiency Assessments of California (ELPAC; for English Learners Only).
Please Note: Computer-based is for all domains grades 3-12. The writing domain is paper-based only for grades K-2. All other domains
for grades K-2 are computer-based.
   Initial ELPAC
       Without Designated Supports (All domains)
       Designated Supports (All domains)
       Without Accommodations (All domains)
       Accommodations (All domains)
```

## Recorded human coverage omissions

_None recorded yet. Use the complete source chunk above to find omissions._

## Items

## Item 00 — `doc_11:chunk:6fa5cd841ec5:raw:000`

### 1. Source passage (item-local excerpt)

> …Page _____ of _____ RIDGEWAY-CORDOVA SELPA ANNUAL GOALS AND OBJECTIVES Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 10/2/2024 Area of Need: Written Expression Measurable Annual Goal #: Goal: By 10/02/2024,…

### 2. Raw model extraction

- predicate: `legal_name`
- value: `Emma Rose Callahan`
- value_text: "Student Name: Emma Rose Callahan"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Student Name: Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Student Name: Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 01 — `doc_11:chunk:6fa5cd841ec5:raw:001`

### 1. Source passage (item-local excerpt)

> …f _____ RIDGEWAY-CORDOVA SELPA ANNUAL GOALS AND OBJECTIVES Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 10/2/2024 Area of Need: Written Expression Measurable Annual Goal #: Goal: By 10/02/2024, when given a writing topic and a graphic organizer…

### 2. Raw model extraction

- predicate: `dob`
- value: `2010-03-22`
- value_text: "Birthdate: 3/22/10"
- assertion: `asserted` · reporter: `None`
- life_stage: `birth` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_002` · predicate=`dob` · value=`2010-03-22` · value_text="Birthdate: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_002` · predicate=`dob` · value=`2010-03-22` · value_text="Birthdate: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 02 — `doc_11:chunk:6fa5cd841ec5:raw:002`

### 1. Source passage (item-local excerpt)

> …ing from the disability scientific notation and roots). While she does not test particularly well in math, Linguistically appropriate she does well on practice problems in her Math 10 class. Transition Goal: Education/Training Employment Independent Living Person(s) Responsible: GE Teacher, SAI Teach…

### 2. Raw model extraction

- predicate: `grade`
- value: `10`
- value_text: "Math 10 class"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **observed silent drop** (`observed_silent_drop`)
- gate/check: `_draft_is_skippable`
- reason: `spurious_grade`
- before→after value: `{'value': '10'}` → `None`

### 4. Ledger / retained fact

- chunk-local: _none_
- legacy cache (no_legacy_match): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 03 — `doc_11:chunk:6fa5cd841ec5:raw:003`

### 1. Source passage (item-local excerpt)

> …een met. Comment: Emma Rose Callahan puts in a lot of work in her Math support class. She is polite, engaged and a joy to teach. Progress Report 3: Summary of Progress: Comment: Annual Review Date: 10/2/2024 Goal met Yes No Comments: Per teacher feedback:9/29/24: Math 1 Foundations has not yet covered the math material listed in Emma Rose Callahan's IEP. It is actually our next unit,…

### 2. Raw model extraction

- predicate: `iep_status`
- value: `active`
- value_text: "Annual Review Date: 10/2/2024"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_003` · predicate=`iep_status` · value=`active` · value_text="Annual Review Date: 10/2/2024" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 04 — `doc_11:chunk:6fa5cd841ec5:raw:004`

### 1. Source passage (item-local excerpt)

> …tion coefficients with the same accuracy. This objective has been met. Comment: Emma Rose Callahan's focus, productivity and accuracy have improved greatly in the past few months. Emma Rose Callahan takes her classwork seriously and helps other students. She is a pleasure to have in class. Progress Report 2: 5/13/2024 Summary of Progress: Given notes and prior practice, Emma Rose Callahan can solve 5 two-step linear equations wit…

### 2. Raw model extraction

- predicate: `attendance`
- value: `regular`
- value_text: "Emma Rose Callahan takes her classwork seriously and helps other students."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `strength`

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

## Item 05 — `doc_11:chunk:6fa5cd841ec5:raw:005`

### 1. Source passage (item-local excerpt)

> …measured by student work samples. Short-Term Objective: Progress Report 1: 12/10/2023 Summary of Progress: When given a writing topic and a graphic organizer, Emma Rose Callahan can write a paragraph expository essay with an emerging topic sentence, 2-3 supporting sentences and a summary conclusion using appropriate grade level language and conventions with at least 70% accuracy as measured by student work samples. This objective has been met. Comment: Emma Rose Callahan is making progress toward this goal. Progress Report 2: 5/24/2024 Summary of Progres…

### 2. Raw model extraction

- predicate: `basic_reading`
- value: `5`
- value_text: "can write a paragraph expository essay with an emerging topic sentence, 2-3 supporting sentences and a summary conclusion using appropriate grade level language and conventions with at least 70% accuracy"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `strength`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_004` · predicate=`basic_reading` · value=`5` · value_text="can write a paragraph expository essay with an emerging topic sentence, 2-3 supporting sentences and a summary conclusion using appropriate grade level language and conventions with at least 70% accuracy" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 06 — `doc_11:chunk:6fa5cd841ec5:raw:006`

### 1. Source passage (item-local excerpt)

> …rds. Short-Term Objective: Progress Report 1: 12/13/2023 Summary of Progress: Given notes and prior practice, Emma Rose Callahan understands the concept of a linear equation and can solve 5 one-step equations with whole number coefficients with at least 90% accuracy in 1/2 trials as measured by student work samples/teacher records. She can also solve one-step equations with decimal and fraction coefficients with the same accuracy. This objective has been m…

### 2. Raw model extraction

- predicate: `math_fluency`
- value: `90`
- value_text: "can solve 5 one-step equations with whole number coefficients with at least 90% accuracy in 1/2 trials"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `strength`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_005` · predicate=`math_fluency` · value=`90` · value_text="can solve 5 one-step equations with whole number coefficients with at least 90% accuracy in 1/2 trials" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._
