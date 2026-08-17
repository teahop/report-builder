# Item comparison — `doc_11_chunk01`

_Diagnostic render from existing targeted-chunk replay artifacts. No new model calls. Chunk-local facts are the trustworthy retained row for this replay. Legacy-cache rows are matched by value_text (not fact id) because the 77-fact cache is `legacy_untraceable` and ids collide across runs._

- source: `doc_11` · IEP — current school records
- source_date: `2024-10-02`
- chunk: `1` / `9`
- chunk_sha256: `9a3d5d2298aafea9b00722226387d629b5fe5ba0c0ccedfa54bd2182d86aaaf6`
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

_This is the full retained source for `chunk_sha256=9a3d5d2298aafea9b00722226387d629b5fe5ba0c0ccedfa54bd2182d86aaaf6`. Use it to identify evidence the model never extracted. Item-local excerpts below cannot expose omissions on their own._

**chunk_sha256:** `9a3d5d2298aafea9b00722226387d629b5fe5ba0c0ccedfa54bd2182d86aaaf6`

```text
a. Purpose of Mee ng/Agenda Review - Annual/Transi on IEP
b. Delivery and review of Procedural Safeguards - Parent conﬁrmed receiving procedural safeguards and waived reviewing them as a team.
c. Mee ng Norms/Time Parameters - 12:00 - 1:00
d. Verify student data (home address/phone number): informa on is up to date.

KNOWING THE STUDENT
2. Present Levels of Academic & Func onal Performance
a. Strengths/Preferences/Interests - Mr. Hollis shared that Emma Rose Callahan is a pleasure to have in class. She is kind and puts her best eﬀort. Mr.
Hollis also shared that Emma Rose Callahan's absences and not dressing down has impacted her grade. He explained that an addi onal uniform was
given to Emma Rose Callahan. Emma Rose Callahan shared she traveled to PE for PAWS for make up points. Mr.Hollis shared that she can also ﬁnd an ar cle related
to health and physical educa on and write a summary about it. Deadline for make up work is right before the end of the quarter. In this case
Oct. 17th but Mr. Hollis is allowing Emma Rose Callahan extended me if needed. No addi onal ques ons or comments for Mr. Hollis and the IEP
team excused him for the remainder of the mee ng.
Ms. R. Alvarez shared the rest of the strengths and interests in and outside of school. See present levels page for
b. Parent concerns related to educa onal progress: Parent is concerned about Biology in par cular and Emma Rose Callahan falling behind. Mom is
concerned that Emma Rose Callahan is struggling to keep up with all of her assignments and work needed for her classes.
Ms. R. Alvarez proposed alt. test accommoda on and notecard to support this area.
c. Review of Results of Statewide Tes ng: CAASPP/CMA/APAC/CAL ALT/CELDT/ Fitnessgram, other Assessment Data/Hearing/Vision:
Reviewed Emma Rose Callahan's SBAC English and Math scores. Went over Edmentum diagnos c test results as well. See present levels for more
informa on.
d. Pre-academic/Academic/Func onal Skills - Went over grades and teacher input forms. See present levels for more informa on.
e. Communica on Development - Appears to be average. Not a concern at this me. See present levels for more informa on.
f. Gross/Fine Motor Development - Appears to be average. Not a concern at this me. See present levels for more informa on.
g. Social-Emo onal/Behavioral - Emma Rose Callahan's behavior is adap ve and does not impede her learning. She is shy which impacts her ability to ask
for help. See present levels for more informa on.
h. Voca onal Skills - Appears to be average. Has good a endance and is able to follow direc ons. Not a concern at this me. See present
levels for more informa on.
i. Adap ve/Daily Living Skills - Appears to be average. See present levels for more informa on.
j. Health - Emma Rose Callahan was diagnosed wit hypothyroid and is on medica on. At this me she is ﬁguring out the right dosage. It does not require a
health plan at this me but if things change then mom will inform IEP team/nurse.
k. Summary of Performance (if Gradua ng Senior or Aging out at 22) - not applicable to this mee ng.
l. Areas of Need
3. Progress towards Goals – Copies given to parent(s) - Old goals were reviewed. IEP team had no addi onal ques ons or comments.
                                                                                                                    Page then
4. Individual Transi on Plan (age 15 and up) - went over Emma Rose Callahan's interview results. She wants to a end community college   _____  of _____
                                                                                                                               transfer to a
4 year. Discussed the areas of need Emma Rose Callahan requires support in. Emma Rose Callahan is on diploma track and should be gradua ng May 2028. Went over
proposed courses for the remainder of her HS years. Transi on goal around career interest will be wri en to support this area.

DEVELOP A PLAN
5. Goals: Development/Adop on - Reviewed proposed goals and IEP team agreed.
6. Par cipa on in Statewide Assessments/CELDT/CAASPP - Emma Rose Callahan will not par cipate in state tes ng as a freshman. Juniors at FHS are the
only ones expected to take it unless seniors didn't take it during their junior year.
7. Special Factors
a. Discussion: Assis ve Technology - Emma Rose Callahan does not require assis ve technology to meet educa onal needs. See special factors page for
more details.
b. Low Incidence, ELL, Behavior - Emma Rose Callahan is not considered low incidence, English learner, and does not have behaviors that impede her
learning.
PLACEMENT AND SERVICES
8. Determina on of Placement & Services
a. Discussion regarding placement op ons. Document considera on of Least Restric ve Environment and Poten al Harmful Eﬀects: Emma Rose Callahan
came into FHS with SAI English and Study Skills. FHS does not oﬀer SAI English as a class and therefore will be placed in the general
educa on se ng with the excep on of study skills. If Emma Rose Callahan were to ever change schools it should be considered that Emma Rose Callahan was supposed
to be oﬀered a 10s level class.
b. Supplementary Aids & Services: Accommoda ons, Modiﬁca ons, & Supports - Emma Rose Callahan kept all of her accommoda ons and the IEP team
discussed and agreed to add: notecard for assessments, word banks provided for assessments, alternate test loca on, and gum to help with
concentra on. Emma Rose Callahan will have SAI Study Skills (258 minutes x weekly) and college and career awareness (15 min monthly each).
c. Related Services, Transporta on, Extended School Year (ESY) Discussion - Emma Rose Callahan does not require transporta on nor ESY. See Oﬀer of
Fape for more details.
9. Summary of District’s Oﬀer of FAPE - Emma Rose Callahan will con nue with services in study skills and had addi onal accommoda ons spending 13%
of the me outside of the regular classroom se ng.
a. Mee ng Comple on/Team Ac on - Mom and IEP team consented to the IEP and all members felt like they par cipated in the IEP
process.
b. Signatures of Consent - Case manager will wrap up notes and update pages, then send an electronic packet signature for parent to review
and sign.
                                                                                                                       Page _____ of _____

RIDGEWAY-CORDOVA SELPA
                                     PRESENT LEVELS OF ACADEMIC ACHIEVEMENT AND FUNCTIONAL
                                                         PERFORMANCE

Student Name: Emma Rose Callahan                                 Birthdate: 3/22/10                     IEP Date: 10/2/2024

Strengths/Preferences/Interests
Emma Rose Callahan is a kind and funny student who likes to draw/paint, shop, watch TV/movies/videos, read, sing, listen to music, learn to play the guitar,
dance, take care of animals and plants, and hang out with friends. Her favorite class is math because she enjoys the subject more than the
other subjects and learns best from Mrs. Reyes. She answers ques ons and helps guide her to answers for her homework.
Parent input and concerns relevant to educational progress
Mom's concern is struggling to keep up with assignments. Biology is a class and wants to know how to use accommoda ons. Ms. R. Alvarez
will ask Mr. Doyle to add her to Google Classroom to help.

Smarter Balanced Assessment Consortium (SBAC)
English/Language Arts
    Not Applicable

English/Language Arts Overall
  Standard Exceeded         Standard Met Standard Nearly Met Standard Not Met
Reading/Listening               Above Standard Near Standard Below Standard
Writing/Research                Above Standard Near Standard Below Standard

Math
   Not Applicable

Math Overall
  Standard Exceeded Standard Met Standard Nearly Met Standard Not Met
Concepts and Procedures Above Standard Near Standard Below Standard
Mathematical Practices  Above Standard Near Standard Below Standard

California Alternate Assessments (CAA)
   Not Applicable
English Language Arts            Understanding      Foundational Understanding       Limited Understanding
Math                             Understanding      Foundational Understanding       Limited Understanding
Science                          Understanding      Foundational Understanding       Limited Understanding

English Language Development Test (English Learners Only)
  Not Applicable

English Language Proficiency Assessments of California (ELPAC)
  Initial ELPAC
  Summative ELPAC
Overall Score: Overall Performance Level:        Oral Language Score/Level:
Written Language Score/Level:

Scores by domain
Listening:                             Speaking:                               Reading:                                  Page _____ of _____
                                                                                                                   Writing:

Performance by domain
Listening:                             Speaking:                               Reading:                            Writing:

Alternate English Language Proficiency Assessments for California (Alternate ELPAC):
   Initial Alternate ELPAC
   Summative Alternate ELPAC
Overall Score:    Overall Performance Level:

Physical Education Testing (grades 5, 7 & 9): N/A

Other Assessment Data (e.g., curriculum assessment, other district assessment, etc.) 2024: Edmentum: the goal of the adap ve
diagnos c is to achieve around 50% correct.
Math: Emma Rose Callahan's diagnos c score of 989 ranks at the 18th na onal percen le. This means Emma Rose Callahan scored higher than 18 percent of students
in the same grade na onally who tested in the Fall.
Algebra & Expressions- 3/11
Frac ons & Ra os - 3/11
Geometry - 3/10
Measurement, Data, & Sta s cs - 1/11
Numbers & Opera ons - 5/11
English: Emma Rose Callahan's diagnos c score of 1,203 ranks at the 62nd na onal percen le. This means Emma Rose Callahan scored higher than 62 percent of
students in the same grade na onally who tested in the Fall.
Language and Vocabulary- 5/14
Reading Literature- 8/15
Reading Informa onal Text- 8/15

23-24 SBAC Science: Grade 8 Science 2 - Standard Nearly Met 388
Hearing Date: 9/7/2023 Pass Fail        Other Maico audiometer at 25 decibels for 500, 1000, 2000, and 4000 Hz.
Near Vision Date: 9/7/2023     Pass Fail     Other Good Lite and sloan le ers, 20/60 binocular; referral sent to mother
Distance Vision Date: 9/7/2023    Pass Fail      Other Good Lite and sloan le ers R20/40, L20/30; referral sent to mother

Preacademic/Academic/Functional Skills
Current grades as of 9/28/204:
IM1 Founda ons: B+
Study Skills: A
Biology: D
Guitar: A
Fitness: C+
English: B-

Teacher Input:
Biology: It appears Emma Rose Callahan is using some of her accommoda ons in class. She does do most if not all of her work given extra me.Emma Rose Callahan
seems to struggle with the material in this class. She did not do well on the Unit 1 test. In the areas of work comple on, group work, ability to
work independently, follows instruc ons, a tude toward learning, a en on/focus, and peer interac ons Emma Rose Callahan appears to be in the
average level.
```

## Recorded human coverage omissions

_None recorded yet. Use the complete source chunk above to find omissions._

## Items

## Item 00 — `doc_11:chunk:9a3d5d2298aa:raw:000`

### 1. Source passage (item-local excerpt)

> …ess/phone number): informa on is up to date. KNOWING THE STUDENT 2. Present Levels of Academic & Func onal Performance a. Strengths/Preferences/Interests - Mr. Hollis shared that Emma Rose Callahan is a pleasure to have in class. She is kind and puts her best eﬀort. Mr. Hollis also shared that Emma Rose Callahan's absences and not dressing down has impacted her grade. He explained that an addi onal uniform…

### 2. Raw model extraction

- predicate: `legal_name`
- value: `Emma Rose Callahan`
- value_text: "Emma Rose Callahan is a pleasure to have in class."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Emma Rose Callahan is a pleasure to have in class." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 01 — `doc_11:chunk:9a3d5d2298aa:raw:001`

### 1. Source passage (item-local excerpt)

> …EVELS OF ACADEMIC ACHIEVEMENT AND FUNCTIONAL PERFORMANCE Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 10/2/2024 Strengths/Preferences/Interests Emma Rose Callahan is a kind and funny student who likes to draw/paint, shop, watch TV/movies/videos, read…

### 2. Raw model extraction

- predicate: `age_years`
- value: `14`
- value_text: "Birthdate: 3/22/10"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_002` · predicate=`age_years` · value=`14` · value_text="Birthdate: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_002` · predicate=`dob` · value=`2010-03-22` · value_text="Birthdate: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 02 — `doc_11:chunk:9a3d5d2298aa:raw:002`

### 1. Source passage (item-local excerpt)

> …be wri en to support this area. DEVELOP A PLAN 5. Goals: Development/Adop on - Reviewed proposed goals and IEP team agreed. 6. Par cipa on in Statewide Assessments/CELDT/CAASPP - Emma Rose Callahan will not par cipate in state tes ng as a freshman. Juniors at FHS are the only ones expected to take it unless seniors didn't take it during their junior year. 7. Special Factors a. Dis…

### 2. Raw model extraction

- predicate: `grade`
- value: `9`
- value_text: "Emma Rose Callahan will not participate in state testing as a freshman."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_003` · predicate=`grade` · value=`9` · value_text="Emma Rose Callahan will not participate in state testing as a freshman." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 03 — `doc_11:chunk:9a3d5d2298aa:raw:003`

### 1. Source passage (item-local excerpt)

> …Callahan will con nue with services in study skills and had addi onal accommoda ons spending 13% of the me outside of the regular classroom se ng. a. Mee ng Comple on/Team Ac on - Mom and IEP team consented to the IEP and all members felt like they par cipated in the IEP process. b. Signatures of Consent - Case manager will wrap up notes and update pages, then send an electronic packet signature for parent to review and…

### 2. Raw model extraction

- predicate: `iep_status`
- value: `in place`
- value_text: "Mom and IEP team consented to the IEP and all members felt like they participated in the IEP process."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'in place'}` → `{'value': 'active'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_004` · predicate=`iep_status` · value=`active` · value_text="Mom and IEP team consented to the IEP and all members felt like they participated in the IEP process." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 04 — `doc_11:chunk:9a3d5d2298aa:raw:004`

### 1. Source passage (item-local excerpt)

> …average. See present levels for more informa on. j. Health - Emma Rose Callahan was diagnosed wit hypothyroid and is on medica on. At this me she is ﬁguring out the right dosage. It does not require a health plan at this me but if things change then mom will inform IEP team/nurse. k. Summary of Performance (if Gradua ng Senior or Aging out at 22) - not applicable to this mee ng. l. Areas of Need…

### 2. Raw model extraction

- predicate: `health_plan_status`
- value: `none`
- value_text: "It does not require a health plan at this time but if things change then mom will inform IEP team/nurse."
- assertion: `denied` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_005` · predicate=`health_plan_status` · value=`none` · value_text="It does not require a health plan at this time but if things change then mom will inform IEP team/nurse." · assertion=`denied` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_009` · predicate=`health_plan_status` · value=`none` · value_text="It does not require a health plan at this time but if things change then mom will inform IEP team/nurse." · assertion=`denied` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 05 — `doc_11:chunk:9a3d5d2298aa:raw:005`

### 1. Source passage (item-local excerpt)

> …ons. Not a concern at this me. See present levels for more informa on. i. Adap ve/Daily Living Skills - Appears to be average. See present levels for more informa on. j. Health - Emma Rose Callahan was diagnosed wit hypothyroid and is on medica on. At this me she is ﬁguring out the right dosage. It does not require a health plan at this me but if things change then mom will inform…

### 2. Raw model extraction

- predicate: `medications`
- value: `hypothyroid medication`
- value_text: "Emma Rose Callahan was diagnosed with hypothyroid and is on medication."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_006` · predicate=`medications` · value=`hypothyroid medication` · value_text="Emma Rose Callahan was diagnosed with hypothyroid and is on medication." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_010` · predicate=`medications` · value=`geodon, gum, hypothyroid medication, trileptal, vyvance` · value_text="Emma Rose Callahan was diagnosed with hypothyroid and is on medication.; She takes the medications Geodon, Trileptal, and Vyvance.; gum - to help with focus/attention/alertness" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 06 — `doc_11:chunk:9a3d5d2298aa:raw:006`

### 1. Source passage (item-local excerpt)

> …els for more informa on. f. Gross/Fine Motor Development - Appears to be average. Not a concern at this me. See present levels for more informa on. g. Social-Emo onal/Behavioral - Emma Rose Callahan's behavior is adap ve and does not impede her learning. She is shy which impacts her ability to ask for help. See present levels for more informa on. h. Voca onal Skills - Appears to be…

### 2. Raw model extraction

- predicate: `behavioral_concern`
- value: `shy`
- value_text: "Emma Rose Callahan's behavior is adaptive and does not impede her learning. She is shy which impacts her ability to ask for help."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_007` · predicate=`behavioral_concern` · value=`shy` · value_text="Emma Rose Callahan's behavior is adaptive and does not impede her learning. She is shy which impacts her ability to ask for help." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_012` · predicate=`basic_reading` · value=`average` · value_text="Emma Rose Callahan's behavior is adaptive and does not impede her learning." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._
