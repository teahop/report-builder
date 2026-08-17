# Item comparison — `doc_11_chunk02`

_Diagnostic render from existing targeted-chunk replay artifacts. No new model calls. Chunk-local facts are the trustworthy retained row for this replay. Legacy-cache rows are matched by value_text (not fact id) because the 77-fact cache is `legacy_untraceable` and ids collide across runs._

- source: `doc_11` · IEP — current school records
- source_date: `2024-10-02`
- chunk: `2` / `9`
- chunk_sha256: `fc9b786c086bdcbda3db99e1df0281969642c2d49223d8e33a2d534484db7189`
- model: `gpt-4o-mini` · origin: `targeted_chunk_replay`
- raw items: **12**

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

_This is the full retained source for `chunk_sha256=fc9b786c086bdcbda3db99e1df0281969642c2d49223d8e33a2d534484db7189`. Use it to identify evidence the model never extracted. Item-local excerpts below cannot expose omissions on their own._

**chunk_sha256:** `fc9b786c086bdcbda3db99e1df0281969642c2d49223d8e33a2d534484db7189`

```text
PE: Emma Rose Callahan when present does well with class ac vi es and following instruc ons. She gives her best eﬀort during all class ac vi es. Areas
where Emma Rose Callahan can improve is her a endance and dressing down in her PE uniform. Emma Rose Callahan and I have spoken about her wearing her PE
uniform to class and I have oﬀered to provide her a 2nd uniform for days that she accidentally leaves one at home. If she is in a endance,
gives her best eﬀort, and dresses down in her uniform she will have success in class. For this class Emma Rose Callahan does not appear to need
accommoda ons. In the areas of group work, ability to work independently, follows instruc ons, a tude toward learning, a en on/focus,
                                                                                                               Page _____ of _____
and peer interac ons Emma Rose Callahan appears to be in the average level. Work comple on is her area of needing improvement.
English: Academically, per the edmentum diagnos c she is reading at a 7th grade reading level- we are working in edmentum daily during
the beginning of class to ﬁll in the gaps in learning. She wil retest in January. She also recently took the ﬁrst vocabulary quiz and received
15/25. She is able to retake during PAWs. Regarding her IEP goals, We have not taken any wri en assessments yet; however, Miss Emma Rose Callahan
works during independent work me, takes notes on her own and asks for clariﬁca on when needed. In the areas of work comple on,
ability to work independently, follows instruc ons, a tude toward learning, a en on/focus, and peer interac ons Emma Rose Callahan appears to be in
the average level. Group work is her only area of needing improvement.

Math:Emma Rose Callahan works very well independently, in stretches, but has expressed a reluctance to work with a partner. Our school's principal, Mr.
Whitfield, has asked the math department to have students work in pairs o en during class, so that students can collaborate to complete
math problems. Emma Rose Callahan is friendly and polite. In the areas of work comple on, ability to work independently, follows instruc ons, a tude
toward learning, a en on/focus, and peer interac ons Emma Rose Callahan appears to be in the average level. Group work is her only area of needing
improvement.

Study Skills: Emma Rose Callahan is a kind student. She is eager to do well in her classes but needs support when it comes to self advoca ng. O en mes
we have discussions about PE and needing to show up prepared as not dressing down is impac ng her grade. She is good about follow
direc ons in class and taking breaks when needed. We will be working on college and career goals in class and working on sending emails to
teachers to communicate our needs. In the areas of work comple on, ability to work independently, follows instruc ons, a tude toward
learning, group work, and peer interac ons Emma Rose Callahan appears to be in the average level. a en on/focus is her only area of needing
improvement.
Communication Development
Emma Rose Callahan doesn’t require high-tech assis ve technology or augmenta ve communica on devices to communicate with staﬀ or peers.
Emma Rose Callahan's communica on development and skills appear to be average. Emma Rose Callahan demonstrates age-appropriate verbal and non-verbal
communica on skills. She is able to communicate her basic wants and needs. According to her English teacher, Emma Rose Callahan responds well to
individual check ins and encouragement from the teacher. Emma Rose Callahan has expressed her diﬃculty asking her help which is an area she will be
ge ng support in study skills.
Gross/Fine Motor Development
Compared to grade-level peers,Emma Rose Callahan’s voca onal skills appear to be on average.
Social Emotional/Behavioral
Her current adap ve behavior appears to be age-appropriate. Emma Rose Callahan is a friendly young girl and very pleasant to talk with. She is engaging
and wants to do well. She is frustrated with her grades at this me and will beneﬁt from much support in terms of accommoda ons. This is
an area to focus on in study skills.
Emma Rose Callahan appears to struggle with mo va on in her classes. At the beginning of the school year, Emma Rose Callahan would regularly fall asleep in class,
speciﬁcally in her morning classes but she is now trying to go out for a break and drink water. Emma Rose Callahan o en feels shy talking 1:1 with her
teachers.
Vocational
Compared to grade-level peers, Emma Rose Callahan's voca onal skills appear to be average. Voca onal skills include: a endance, work habits, ini a ve,
work comple on, punctuality,following direc ons, etc. Emma Rose Callahan's a endance seems good at this me. She is working on establishing
be ering work habits. She is able to complete most of her work and is able to show up on me to classes. She is able to follow direc ons with
minimal prompts.
Adaptive/Daily Living Skills
Compared to grade-level peers, Emma Rose Callahan’s independent func oning appears to be on average. She is able to take care of her personal needs
on her own.
Health
2024: Hypothyroid - no health plan needed at this me. If things change mom will contact school or case manager.
9/28/23-Summary/Recommenda ons:
Emma Rose Callahan is a healthy girl. She has RAD and ADHD. She takes the medica ons Geodon, Trileptal, and Vyvance. All medica ons are taken at
home. She has no known allergies. She receives regular medical and dental care. She may be due for a dental visit. ShePage    _____
                                                                                                                          passed      of _____
                                                                                                                                 the hearing
screening, but she did not pass the vision screening. The results were shared with her mother and a vision referral sent home. She should be
able to par cipate in classroom and school related ac vi es without restric ons due to her health status; although she would beneﬁt from
glasses. Please no fy the school nurse of any changes to her health. Please see a ached health report for further details.
Ashley Bloom, RN Creden aled School Nurse
4/25/19
Hearing PASSED with both ears using the Ambco 650A pure tone audiometer.
Vision PASSED with both eyes without glasses using the HOTV chart for distance and the ETDRS chart for near vision.
Emma Rose Callahan appears healthy and stated she has no concerns. She had her appendix out earlier this month (4/1/19) but she said she isn't having
any problems from that. According to the H&D completed on 4/10/19 by mom, Emma Rose Callahan has a history of ADHD, a sensi vity to noise/touch,
sleep problems, and seasonal allergies. She last saw her den st 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of
melatonin at night. Emma Rose Callahan was adopted at 19 months so informa on on birth is limited. She met all of her developmental milestones on
  me except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an
unusually loud voice.
Per mom, Emma Rose Callahan is ge ng ﬁ ed for a CPAP machine and will be part of a sleep study over summer.
Does this student have an Individual Health Plan?           Yes     No

For student to receive educational benefit, goals will be written to address the following areas of need:
Math ﬂuency and wri en expression and transi on.
                                                                                                                       Page _____ of _____

RIDGEWAY-CORDOVA SELPA
                                                    INDIVIDUAL TRANSITION PLANNING (ITP)

Student Name: Emma Rose Callahan                                 Date of Birth: 3/22/10                 IEP Date: 10/2/2024

If Appropriate, and agreed upon, agencies invited:
Student Invited:   Yes     No
                                                                          Yes No N/A
Describe how the student participated in the process:       Present At Meeting Interview Prior Interest Inventories Questionnaire

Age-appropriate transition assessments/instruments were used:         Yes     No

Describe the results of the assessments:
Strengths/ Interests:

Emma Rose Callahan describes herserlf as: Loving/Caring, Friendly/Kind, Giving, Mo vated, Intelligent, Crea ve, Funny, Though ul, Hard-working,
Independent, Responsible. She considers her academic strengths to include: Ge ng to school and/or class on me, Following school rules,
Working well with teachers, Working well with classmates, Par cipa ng in class, Learning new things quickly. She learns best from Mrs.
Reyes, her English teacher.

Her ideal/dream job is to do something involving equine therapy. Currently she does not have any work experience but has some
community service experience as she helps out in her neighborhood. Emma Rose Callahan is mo vated by: Herself, family, desire to succeed in life, My
future goals. Emma Rose Callahan does not want to fail.

Areas of Need

Emma Rose Callahan feels like she struggles with and/or needs help with: Comple ng my work, Asking for help when I'm confused, Understanding new
concepts that are hard for me, Managing my frustra on when I ﬁnd something challenging. Her most diﬃcult class at this me is Biology
because she feels like she doesn't have me to ﬁnish her work. Emma Rose Callahan also feels like she has a hard me with mo va on. She feels like in
general her classwork is too hard for her.

Emma Rose Callahan feels like some things her teachers can do to help her is: Give me extra me to complete assignments and tests, Check-in with me
regularly to make sure I'm doing things correctly, Highlight, underline, or embolden key informa on, Use visuals (or pictures) to explain a
new concept, Give plenty of examples when teaching something new.

Post HS plans: Emma Rose Callahan wants to go to community college and then transfer to a 4 year college.
                                 Student's Post Secondary Goal Training or Education (Required):
Upon completion of school I will go to community college.       Transition Service Code as Appropriate:

Activities to Support Post Secondary Goal:
                                                                        visit the counseling oﬃce to meet with college and career point of
                                                                        contact.
                                                                        Community Experiences as Appropriate:
Linked to Annual Goal # 1                                               Related Services as Appropriate:
Person/Agency Responsible: Student, Special Educa on Teacher

Student's Post Secondary Goal Employment (Required):
Upon completion of school I will Work in the ﬁeld of equine therapy. Transition Service Code as Appropriate:
                                                                                                      Page _____ of _____
                                                               Activities to Support Post Secondary Goal:
                                                               Work with workability to see if they can support her with community
                                                               service/work experience related to this ﬁeld.
                                                               Community Experiences as Appropriate:

Linked to Annual Goal # 1                                      Related Services as Appropriate:
Person/Agency Responsible: Student, Special Educa on Teacher

Student's Post Secondary Goal Independent Living (As appropriate):
Upon completion of school I will                               Transition Service Code as Appropriate:

Activities to Support Post Secondary Goal:

Community Experiences as Appropriate:
```

## Recorded human coverage omissions

_None recorded yet. Use the complete source chunk above to find omissions._

## Items

## Item 00 — `doc_11:chunk:fc9b786c086b:raw:000`

### 1. Source passage (item-local excerpt)

> PE: Emma Rose Callahan when present does well with class ac vi es and following instruc ons. She gives her best eﬀort during all class ac vi es. Areas where Emma Rose Callahan can improve is her a endan…

### 2. Raw model extraction

- predicate: `legal_name`
- value: `Emma Rose Callahan`
- value_text: "Emma Rose Callahan"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_001` · predicate=`legal_name` · value=`Emma Rose Callahan` · value_text="Student Name: Emma Rose Callahan" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 01 — `doc_11:chunk:fc9b786c086b:raw:001`

### 1. Source passage (item-local excerpt)

> …RIDGEWAY-CORDOVA SELPA INDIVIDUAL TRANSITION PLANNING (ITP) Student Name: Emma Rose Callahan Date of Birth: 3/22/10 IEP Date: 10/2/2024 If Appropriate, and agreed upon, agencies invited: Student Invited: Yes No…

### 2. Raw model extraction

- predicate: `dob`
- value: `2010-03-22`
- value_text: "Date of Birth: 3/22/10"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_002` · predicate=`dob` · value=`2010-03-22` · value_text="Date of Birth: 3/22/10" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 02 — `doc_11:chunk:fc9b786c086b:raw:002`

### 1. Source passage (item-local excerpt)

> …__ and peer interac ons Emma Rose Callahan appears to be in the average level. Work comple on is her area of needing improvement. English: Academically, per the edmentum diagnos c she is reading at a 7th grade reading level- we are working in edmentum daily during the beginning of class to ﬁll in the gaps in learning. She wil retest in January. She also recently took the ﬁrst vocabulary quiz and rece…

### 2. Raw model extraction

- predicate: `grade`
- value: `7`
- value_text: "she is reading at a 7th grade reading level"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **observed silent drop** (`observed_silent_drop`)
- gate/check: `_draft_is_skippable`
- reason: `spurious_grade`
- before→after value: `{'value': '7'}` → `None`

### 4. Ledger / retained fact

- chunk-local: _none_
- legacy cache (no_legacy_match): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 03 — `doc_11:chunk:fc9b786c086b:raw:003`

### 1. Source passage (item-local excerpt)

> ⚠️ **Passage not located in the full chunk text.**
>
> Needle: "She takes the medications Geodon, Trileptal, and Vyvance."
>
> This is a human-review question — not an automatic hallucination label. Resolve against the complete source chunk above before deciding.

### 2. Raw model extraction

- predicate: `medications`
- value: `Geodon, Trileptal, Vyvance`
- value_text: "She takes the medications Geodon, Trileptal, and Vyvance."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'Geodon, Trileptal, Vyvance'}` → `{'value': 'geodon, trileptal, vyvance'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_003` · predicate=`medications` · value=`geodon, trileptal, vyvance` · value_text="She takes the medications Geodon, Trileptal, and Vyvance." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_010` · predicate=`medications` · value=`geodon, gum, hypothyroid medication, trileptal, vyvance` · value_text="Emma Rose Callahan was diagnosed with hypothyroid and is on medication.; She takes the medications Geodon, Trileptal, and Vyvance.; gum - to help with focus/attention/alertness" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 04 — `doc_11:chunk:fc9b786c086b:raw:004`

### 1. Source passage (item-local excerpt)

> …d to grade-level peers, Emma Rose Callahan’s independent func oning appears to be on average. She is able to take care of her personal needs on her own. Health 2024: Hypothyroid - no health plan needed at this me. If things change mom will contact school or case manager. 9/28/23-Summary/Recommenda ons: Emma Rose Callahan is a healthy girl. She has RAD and ADHD. She takes the medica…

### 2. Raw model extraction

- predicate: `health_plan_status`
- value: `none`
- value_text: "no health plan needed at this time"
- assertion: `denied` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_004` · predicate=`health_plan_status` · value=`none` · value_text="no health plan needed at this time" · assertion=`denied` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 05 — `doc_11:chunk:fc9b786c086b:raw:005`

### 1. Source passage (item-local excerpt)

> ⚠️ **Passage not located in the full chunk text.**
>
> Needle: "Emma Rose Callahan's attendance seems good at this time."
>
> This is a human-review question — not an automatic hallucination label. Resolve against the complete source chunk above before deciding.

### 2. Raw model extraction

- predicate: `attendance`
- value: `good`
- value_text: "Emma Rose Callahan's attendance seems good at this time."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_005` · predicate=`attendance` · value=`good` · value_text="Emma Rose Callahan's attendance seems good at this time." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 06 — `doc_11:chunk:fc9b786c086b:raw:006`

### 1. Source passage (item-local excerpt)

> …gaging and wants to do well. She is frustrated with her grades at this me and will beneﬁt from much support in terms of accommoda ons. This is an area to focus on in study skills. Emma Rose Callahan appears to struggle with mo va on in her classes. At the beginning of the school year, Emma Rose Callahan would regularly fall asleep in class, speciﬁcally in her morning classes but she is now trying…

### 2. Raw model extraction

- predicate: `behavioral_concern`
- value: `motivation`
- value_text: "Emma Rose Callahan appears to struggle with motivation in her classes."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `concern`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_006` · predicate=`behavioral_concern` · value=`motivation` · value_text="Emma Rose Callahan appears to struggle with motivation in her classes." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_013` · predicate=`behavioral_concern` · value=`motivation` · value_text="Emma Rose Callahan appears to struggle with motivation in her classes." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 07 — `doc_11:chunk:fc9b786c086b:raw:007`

### 1. Source passage (item-local excerpt)

> …24: Hypothyroid - no health plan needed at this me. If things change mom will contact school or case manager. 9/28/23-Summary/Recommenda ons: Emma Rose Callahan is a healthy girl. She has RAD and ADHD. She takes the medica ons Geodon, Trileptal, and Vyvance. All medica ons are taken at home. She has no known allergies. She receives regular medical and dental care. She may be du…

### 2. Raw model extraction

- predicate: `trauma_history`
- value: `RAD, ADHD`
- value_text: "She has RAD and ADHD."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'RAD, ADHD'}` → `{'value': 'rad, adhd'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_007` · predicate=`trauma_history` · value=`rad, adhd` · value_text="She has RAD and ADHD." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (no_legacy_match): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 08 — `doc_11:chunk:fc9b786c086b:raw:008`

### 1. Source passage (item-local excerpt)

> …er den st 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so informa on on birth is limited. She met all of her developmental milestones on me except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Per mom, Emma Rose Callaha…

### 2. Raw model extraction

- predicate: `developmental_history`
- value: `typical`
- value_text: "met all of her developmental milestones on time"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_008` · predicate=`developmental_history` · value=`typical` · value_text="met all of her developmental milestones on time" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_015` · predicate=`developmental_history` · value=`typical` · value_text="She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 09 — `doc_11:chunk:fc9b786c086b:raw:009`

### 1. Source passage (item-local excerpt)

> …ingular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so informa on on birth is limited. She met all of her developmental milestones on me except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Per mom, Emma Rose Callahan is ge ng ﬁ ed for a CPAP machine and…

### 2. Raw model extraction

- predicate: `walked_age_months`
- value: `19`
- value_text: "walking at about 19 mos"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `hedged` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_009` · predicate=`walked_age_months` · value=`19` · value_text="walking at about 19 mos" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_015` · predicate=`developmental_history` · value=`typical` · value_text="She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 10 — `doc_11:chunk:fc9b786c086b:raw:010`

### 1. Source passage (item-local excerpt)

> …nin at night. Emma Rose Callahan was adopted at 19 months so informa on on birth is limited. She met all of her developmental milestones on me except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Per mom, Emma Rose Callahan is ge ng ﬁ ed for a CPAP machine and will be part of a sleep st…

### 2. Raw model extraction

- predicate: `first_words_age_months`
- value: `24`
- value_text: "talking at about 2 yrs"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `hedged` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_010` · predicate=`first_words_age_months` · value=`24` · value_text="talking at about 2 yrs" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (value_text_match): `f_doc_11_015` · predicate=`developmental_history` · value=`typical` · value_text="She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs." · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 11 — `doc_11:chunk:fc9b786c086b:raw:011`

### 1. Source passage (item-local excerpt)

> …ahan was adopted at 19 months so informa on on birth is limited. She met all of her developmental milestones on me except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Per mom, Emma Rose Callahan is ge ng ﬁ ed for a CPAP machine and will be part of a sleep study over summer. Does this student…

### 2. Raw model extraction

- predicate: `two_word_phrases_age_months`
- value: `36`
- value_text: "used sentences at about 3 yrs"
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2024-10-02`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_11_011` · predicate=`two_word_phrases_age_months` · value=`36` · value_text="used sentences at about 3 yrs" · assertion=`asserted` · reporter=`None` · as_of_date=`2024-10-02`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._
