# Item comparison — `doc_25_chunk03`

_Diagnostic render from existing targeted-chunk replay artifacts. No new model calls. Chunk-local facts are the trustworthy retained row for this replay. Legacy-cache rows are matched by value_text (not fact id) because the 77-fact cache is `legacy_untraceable` and ids collide across runs._

- source: `doc_25` · IEP — Fairhaven initial (4th grade)
- source_date: `2019-05-29`
- chunk: `3` / `4`
- chunk_sha256: `c70e8192a71c6521965d635cead1227d3b56bd2e8e7cfdcf7cd0474b3273c25a`
- model: `gpt-4o-mini` · origin: `targeted_chunk_replay`
- raw items: **6**

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

_This is the full retained source for `chunk_sha256=c70e8192a71c6521965d635cead1227d3b56bd2e8e7cfdcf7cd0474b3273c25a`. Use it to identify evidence the model never extracted. Item-local excerpts below cannot expose omissions on their own._

**chunk_sha256:** `c70e8192a71c6521965d635cead1227d3b56bd2e8e7cfdcf7cd0474b3273c25a`

```text
SPECIAL EDUCATION and RELATED SERVICES
Service: Specialized Academic Instruction                                                   Start Date: 11/19/2019         End Date: 5/28/2020
Provider: District of Service                                                                   Ind    Grp    Sec Transition
Duration/Freq: 240 min served Weekly                                                        Location: Regular classroom/public day school
Comments: Services will be provided as follows: 240 weekly minutes. SAI support services will be provided within the
general education classroom as a push in model.
Service: Specialized Academic Instruction                                                   Start Date: 5/29/2019          End Date: 11/18/2019
Provider: District of Service                                                                   Ind    Grp    Sec Transition
                                                                                            Location: Separate classroom in public
Duration/Freq: 240 min served Weekly
                                                                                            integrated facility
                                                                                                                              Page _____ of _____

Comments: Services will be provided as follows: 240 weekly minutes. Services will follow the school calendar and may be
interrupted due to assemblies, field trips, special school wide events, minimum days, clinician meetings, and student
absences. Specialized Academic Instruction services are not provided the first two weeks and the last week of the school
year to allow for coordination/consultation/planning.
 Programs and services will be provided according to where student is in attendance and consistent with the district of service calendar and
 scheduled services, excluding holidays, vacations, and non-instructional days unless otherwise specified.
Special Education Transportation         Yes No Parents can provide transportation to and from school.

EXTENDED SCHOOL YEAR (ESY)
                                                                       Yes      No
Rationale: ESY is not required as Emma Rose Callahan is able to recoup lost skills within an appropriate amount of time upon return to school in the Fall.
 Programs and services will be provided according to where student is in attendance and consistent with the district of service calendar and
 scheduled services, excluding holidays, vacations, and non-instructional days unless otherwise specified.
                                                                                                                           Page _____ of _____

PLACER COUNTY SELPA
                                                                   OFFER OF FAPE - EDUCATIONAL SETTING

Student Name: Emma Rose Callahan                                   Birthdate: 3/22/10                       IEP Date: 5/29/2019

Physical Education:              General            Specially Designed              Other

District of Service: EASTERN SIERRA                                                                     School of Attendance: Creekside Oaks

All special education services provided at student’s school of residence?             Yes    No (rationale)   Riverbend Elementary
School is the overflow school for Oak Meadow School Elementary School.
Preschool Program Setting (Ages 3-5 only, including those in TK and Kindergarten):
(Note: Answer items below for students ages 3-5 in Regular Early Childhood Program or Kindergarten)

The location where the student receives the majority of their special education services:
    Same as above    Different from above
Is the Regular Early Childhood Program or Kindergarten Program ten hours per week or greater?                   Yes   No

Program Setting (Ages 6 and older within duration of this IEP): Regular Classroom/Public Day School
(Note: Percentage of time is required for those that will be age 6 and older within the duration of this IEP)
0 % of time student is outside the regular class & extracurricular & non academic activities
100 % of time student is in the regular class & extracurricular & non academic activities
Student will not participate in the regular class and/or extracurricular and/or non academic activities: because

Other Agency Services
  County Mental Health
  California Children's Services(CCS)
  Regional Center
  Probation
  Department of Rehabilitation
  Department of Social Services (DSS)
  Other

Promotion Criteria:               District     Progress on Goals         Other

Parents will be informed of
progress:                         Quarterly    Trimester    Semester        Other

How?                              Progress Summary Report          Other Standards Based Report Card

ACTIVITIES TO SUPPORT TRANSITION (e.g. preschool to kindergarten, special education and/or NPS to general education class, 8th-9th grade, etc)
                                                                                                             Page _____ of _____

PLACER COUNTY SELPA
                                                                   IEP TEAM MEETING NOTES

Student Name: Emma Rose Callahan                            Birthdate: 3/22/10                  IEP Date: 5/29/2019

Date: 5/29/2019

Notes: The purpose of this meeting: Initial IEP to discuss eligibility for special education supports/services.

Those in Attendance:

Mark Rodriguez - Admin.
LeAnne Dolce - Special Education Teacher
Alyssa Onaka - School Psychologist
Shannon Reed - Classroom Teacher
Diane Callahan - Mother

Excusal form signed for School Nurse.

Introductions made and Procedural Safeguards given, Parent did not have any questions related to the Safeguards.
Present Levels in all domains were reviewed with parent and documented on present levels page.

Multi-Disciplinary report reviewed with IEP team members present.

Emma Rose Callahan maintains age appropriate skill sets in the following areas: Communication, Gross/Fine Motor, Vocational, Adaptive
Daily Living.

Health:
Hearing PASSED with both ears using the Ambco 650A pure tone audiometer.
Vision PASSED with both eyes without glasses using the HOTV chart for distance and the ETDRS chart for near vision.

Emma Rose Callahan appears healthy and stated she has no concerns. She had her appendix out earlier this month (4/1/19) but she
said she isn't having any problems from that. According to the H&D completed on 4/10/19 by mom, Emma Rose Callahan has a history
of ADHD, a sensitivity to noise/touch, sleep problems, and seasonal allergies. She last saw her dentist 7/2018. She takes
1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so information
on birth is limited. She met all of her developmental milestones on time except walking at about 19 mos and talking at
about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice.

Eligibility:
The team discussed and documented the service options considered for Emma Rose Callahan. Emma Rose Callahan meets eligibility criteria under the
category of Specific Learning Disability and Other Health Impairment.

Offer of FAPE:
The District recommended and proposed as their offer of FAPE that Emma Rose Callahan receive Specialized Academic Instruction (SAI) in
the Resource Specialist Program (RSP) setting for 240 weekly minutes as a pull out service.

Emma Rose Callahan will also receive short-term counseling with the school psychologist/counselor to review self-regulation strategies,
coping techniques, and check-in during transition for fourth grade year from 5/29/2019-11/29/2019, 2 times per month
for 30 minutes in a separate classroom setting.
Annual goals were drafted in the following areas: Reading Fluency/Comprehension, Writing, Math Word Problems.
                                                                                                      Page _____ of _____

Accommodations and Modifications:
Accommodations and Modifications to the general education curriculum were discussed and documented.

Participation in District and Statewide Assessments were discussed and documented. Accommodations were added for
English Language Arts and Math.

Extended School Year (ESY) services were discussed and not recommended at this time.
Educational Setting:
The educational setting for Emma Rose Callahan to receive special education services were discussed and documented.

Parent signed in agreement to all parts of the IEP and received a copy for their records. The IEP meeting was adjourned.
```

## Recorded human coverage omissions

_None recorded yet. Use the complete source chunk above to find omissions._

## Items

## Item 00 — `doc_25:chunk:c70e8192a71c:raw:000`

### 1. Source passage (item-local excerpt)

> …Page _____ of _____ PLACER COUNTY SELPA OFFER OF FAPE - EDUCATIONAL SETTING Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 5/29/2019 Physical Education: General Specially Designed…

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

## Item 01 — `doc_25:chunk:c70e8192a71c:raw:001`

### 1. Source passage (item-local excerpt)

> …TY SELPA OFFER OF FAPE - EDUCATIONAL SETTING Student Name: Emma Rose Callahan Birthdate: 3/22/10 IEP Date: 5/29/2019 Physical Education: General Specially Designed Other District of Service: EASTERN SIERRA…

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

## Item 02 — `doc_25:chunk:c70e8192a71c:raw:002`

### 1. Source passage (item-local excerpt)

> …ns considered for Emma Rose Callahan. Emma Rose Callahan meets eligibility criteria under the category of Specific Learning Disability and Other Health Impairment. Offer of FAPE: The District recommended and proposed as their offer of FAPE that Emma Rose Callahan receive Specialized Academic Instruction (SAI) in the Resource Specialist Program (RSP) setting for 240 weekly minutes as a pull out service. Emma Rose Callahan will also receive short-term counseling with the school psychologist/counselor to review self-regulation strategies, coping techniques, and check-in during tra…

### 2. Raw model extraction

- predicate: `iep_status`
- value: `in place`
- value_text: "The District recommended and proposed as their offer of FAPE that Emma Rose Callahan receive Specialized Academic Instruction (SAI) in the Resource Specialist Program (RSP) setting for 240 weekly minutes as a pull out service."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **transformed** (`transformed`)
- gate/check: `normalize_value`
- reason: `normalize_value`
- before→after value: `{'value': 'in place'}` → `{'value': 'active'}`

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_003` · predicate=`iep_status` · value=`active` · value_text="The District recommended and proposed as their offer of FAPE that Emma Rose Callahan receive Specialized Academic Instruction (SAI) in the Resource Specialist Program (RSP) setting for 240 weekly minutes as a pull out service." · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (fact_id_collision_different_content): _none_

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 03 — `doc_25:chunk:c70e8192a71c:raw:003`

### 1. Source passage (item-local excerpt)

> …e H&D completed on 4/10/19 by mom, Emma Rose Callahan has a history of ADHD, a sensitivity to noise/touch, sleep problems, and seasonal allergies. She last saw her dentist 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so information on birth is limited. She met all of her developmental milestones on time except walking at about 19 mos and talking at a…

### 2. Raw model extraction

- predicate: `health_plan_status`
- value: `active`
- value_text: "She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_004` · predicate=`health_plan_status` · value=`active` · value_text="She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night." · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_010` · predicate=`medications` · value=`1mg guanfacine, 2.5mg melatonin, 5mg singular` · value_text="She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 04 — `doc_25:chunk:c70e8192a71c:raw:004`

### 1. Source passage (item-local excerpt)

> …her dentist 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so information on birth is limited. She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unusually loud voice. Eligibility: The team discussed and documented the service options considered for Emma Rose…

### 2. Raw model extraction

- predicate: `developmental_history`
- value: `typical with delays`
- value_text: "She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_005` · predicate=`developmental_history` · value=`typical with delays` · value_text="She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs." · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_008` · predicate=`developmental_history` · value=`typical` · value_text="met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs" · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._

## Item 05 — `doc_25:chunk:c70e8192a71c:raw:005`

### 1. Source passage (item-local excerpt)

> …sensitivity to noise/touch, sleep problems, and seasonal allergies. She last saw her dentist 7/2018. She takes 1mg of guanfacine, 5mg of Singular and 2.5 mg of melatonin at night. Emma Rose Callahan was adopted at 19 months so information on birth is limited. She met all of her developmental milestones on time except walking at about 19 mos and talking at about 2 yrs. She used sentences at about 3 yrs. She has been known to have an unu…

### 2. Raw model extraction

- predicate: `trauma_history`
- value: `adopted at 19 months`
- value_text: "Emma Rose Callahan was adopted at 19 months so information on birth is limited."
- assertion: `asserted` · reporter: `None`
- life_stage: `current` · as_of_date: `2019-05-29`
- confidence: `stated` · valence: `neutral`

### 3. Transformation / drop

- disposition: **retained** (`retained`)

### 4. Ledger / retained fact

- chunk-local: `f_doc_25_006` · predicate=`trauma_history` · value=`adopted at 19 months` · value_text="Emma Rose Callahan was adopted at 19 months so information on birth is limited." · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`
- legacy cache (value_text_match): `f_doc_25_019` · predicate=`trauma_history` · value=`adopted at 19 months` · value_text="Emma Rose Callahan was adopted at 19 months so information on birth is limited." · assertion=`asserted` · reporter=`None` · as_of_date=`2019-05-29`

### 5. Human item review (append-only)

_No human item review recorded yet._
