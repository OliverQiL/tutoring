# Tuition Management Platform

My full-stack tuition management platform connecting **Student Data, Educational Resources, Intelligent / Automated Workflows, Financial Records**

## Architecture

![Simple Architecture Diagram](/diagrams/tutoring_architecture.png)

## Tech Stack

| Layer | Tech |
|---|---|
| Programming Language | Python |
| API | FastAPI|
| Structured Database | PostgreSQL |
| ORM | SQLAlchemy + SQL |
| Object Storage | Supabase | 
| Data Processing | pandas |
| Document Extraction | PyMuPDF |
| LLM Integration | Some LLM API |
| Semantic Search | pgvector |
| User Interface | Streamlit |
| Testing | pytest |
| Version Control | Git + Github |

## 1.1 Starting

### Objectives

1. Design SQL Schema

   - ER Diagram

   - SQL Configuration Script ([`sql/create_tables.sql`](/sql/create_tables.sql), PostgreSQL 15+)

   - Locally hosted

2. Python Ingestion + Processing Pipeline

   - CSV-to-database pipeline

   - PDF-to-database pipeline

3. Test Pipeline

   - Real CSV Data

   - Sample PDF Paper

### Implementation Notes

**User Story for ER Diagram:**

As a private tutor, I manage multiple students, each with their own academic background, including their name, school, academic level, and academic programme (e.g., Singapore Mainstream, Integrated Programme, or International Baccalaureate). Each student may receive tuition in one or more subjects, depending on their academic level and programme. I want to maintain records of my students and the subjects I teach them.

The platform should organize educational content according to the hierarchy **Academic Programme → Academic Level → Subject → Topic → Chapter**. For example, Primary 4 Science under the Singapore Mainstream curriculum may contain the topic **Matter**, which includes chapters such as **Properties of Matter** and **States of Matter**. Question content is classified by topics and chapters, while its response format and assessed skills are tracked separately. A question may assess concepts from multiple chapters or topics.

I maintain a collection of educational resources, primarily examination papers and practice exercises, which I want to organize and make searchable. Each resource should be associated with its relevant curriculum, subject, academic level, and source information, and may contain zero questions while awaiting extraction. Individual questions should have attributes such as question number, content, maximum marks, difficulty, and original page reference. Questions may be associated with multiple topics, chapters, and skills, and have a primary response format, allowing me to retrieve relevant practice materials according to specific learning objectives. The original PDF and image files should remain accessible alongside their extracted content.

I also want to manage my tuition lessons and associated financial records. Each lesson takes place on a particular date, involves one student, and may cover one or more subjects. For every session, I want to record its duration, applicable hourly rate, total fee, and payment history. Tuition rates may differ between students and change over time, so historical lesson fees must remain accurate. Lessons may also incur expenses, such as transportation, which should be recorded individually with their category, description, date, and amount.

The platform should allow me to track tuition revenue, outstanding payments, expenses, and net earnings over time, including breakdowns by student. Financial records should remain logically separate from curriculum and educational resources while retaining their relationships with students and lessons.

![ERD](/diagrams/ERD_2.png)
*For simplicity, only the primary keys are illustrated in the ERD. Refer below for full list of attributes:*

## Entity Attributes

### Students
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `student_id` | BIGINT | Primary Key (PK), auto-generated |
| `full_name` | VARCHAR(150) | NOT NULL |
| `school` | VARCHAR(150) | Optional |
| `academic_level` | VARCHAR(50) | NOT NULL |
| `curriculum` | VARCHAR(100) | NOT NULL |

**Primary Key:** `student_id`

### Subjects
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `subject_id` | BIGINT | Primary Key (PK), auto-generated |
| `name` | VARCHAR(100) | NOT NULL |
| `academic_level` | VARCHAR(50) | NOT NULL |
| `curriculum` | VARCHAR(100) | NOT NULL |
| `description` | TEXT | Optional |

**Primary Key:** `subject_id`

**Composite Candidate Key:** (`name`, `academic_level`, `curriculum`)

**Unique Constraint:** `UNIQUE(name, academic_level, curriculum)`

### Topics
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `topic_id` | BIGINT | Primary Key (PK), auto-generated |
| `subject_id` | BIGINT | FK → subjects.subject_id, NOT NULL |
| `name` | VARCHAR(150) | NOT NULL |
| `description` | TEXT | Optional |

**Primary Key:** `topic_id`

**Foreign Key:** `subject_id` → `subjects.subject_id`

**Unique Constraint:** `UNIQUE(subject_id, name)`

### Chapters
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `chapter_id` | BIGINT | Primary Key (PK), auto-generated |
| `topic_id` | BIGINT | FK → topics.topic_id, NOT NULL |
| `name` | VARCHAR(150) | NOT NULL |
| `description` | TEXT | Optional |

**Primary Key:** `chapter_id`

**Foreign Key:** `topic_id` → `topics.topic_id`

**Unique Constraint:** `UNIQUE(topic_id, name)`

### Resources
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `resource_id` | BIGINT | Primary Key (PK), auto-generated |
| `subject_id` | BIGINT | FK → subjects.subject_id, NOT NULL |
| `title` | VARCHAR(255) | NOT NULL |
| `resource_type` | VARCHAR(30) | `exam` / `worksheet` / `exercise`; optional |
| `publication_year` | INTEGER | Optional |
| `file_path` | TEXT | NOT NULL |
| `file_type` | VARCHAR(20) | `pdf` / `png` / `jpeg`; optional |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT 'uploaded'; `uploaded` / `processing` / `review_required` / `completed` / `failed` |
| `uploaded_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

**Primary Key:** `resource_id`

**Foreign Key:** `subject_id` → `subjects.subject_id`

### Questions
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `question_id` | BIGINT | PK, auto-generated |
| `resource_id` | BIGINT | FK → resources.resource_id, NOT NULL |
| `format_id` | BIGINT | FK → question_formats.format_id, optional |
| `question_number` | VARCHAR(30) | NOT NULL; e.g., 1, 2(a), 5(b)(ii) |
| `section` | VARCHAR(20) | Optional; e.g., A, B, C |
| `question_text` | TEXT | Optional during extraction |
| `marks` | NUMERIC(5,2) | Optional, CHECK (marks >= 0) |
| `difficulty` | VARCHAR(20) | `easy` / `medium` / `hard`; optional |
| `page_number` | INTEGER | Optional, CHECK (page_number > 0) |
| `image_path` | TEXT | Optional |
| `classification_status` | VARCHAR(30) | NOT NULL, DEFAULT 'unclassified'; `unclassified` / `review_required` / `classified` |

**Primary Key:** `question_id`

**Foreign Key:** `resource_id` → `resources.resource_id`, `format_id` → `question_formats.format_id`

**Unique Constraint:** `UNIQUE NULLS NOT DISTINCT (resource_id, section, question_number)`

### Question Formats
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `format_id` | BIGINT | PK, auto-generated |
| `name` | VARCHAR(100) | NOT NULL, UNIQUE |
| `description` | TEXT | Optional |

**Primary Key:** `format_id`

### Skills
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `skill_id` | BIGINT | PK, auto-generated |
| `name` | VARCHAR(150) | NOT NULL, UNIQUE |
| `description` | TEXT | Optional |

**Primary Key:** `skill_id`

### Assessments
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `assessment_id` | BIGINT | PK, auto-generated |
| `student_id` | BIGINT | FK → students.student_id, NOT NULL |
| `title` | VARCHAR(255) | NOT NULL |
| `assessment_date` | DATE | Optional until attempted |
| `assessment_type` | VARCHAR(30) | `exam` / `test` / `homework` / `practice` / `diagnostic`; optional |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'draft'; `draft` / `assigned` / `submitted` / `graded` |
| `source_type` | VARCHAR(30) | `full_resource` / `selected_questions` / `mixed_resources` / `original`; optional |
| `notes` | TEXT | Optional |

**Primary Key:** `assessment_id`

**Foreign Key:** `student_id` → `students.student_id`

Each assessment belongs to exactly one student.

An assessment represents a particular collection of questions assigned to or attempted by a student. It may consist of an entire resource, selected questions from one resource, or questions from multiple resources.

The `assessment_type` describes the purpose of the assessment, while `source_type` describes how its questions were assembled.

Repeated attempts of the same paper or question set are represented by separate assessment records. Draft assessments may contain no questions; assigned, submitted, and graded assessments must contain at least one.

---

### Lessons

| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `lesson_id` | BIGINT | PK, auto-generated |
| `student_id` | BIGINT | FK → students.student_id, NOT NULL |
| `lesson_date` | DATE | NOT NULL |
| `duration_minutes` | INTEGER | NOT NULL, CHECK (duration_minutes > 0) |
| `hourly_rate` | NUMERIC(10,2) | NOT NULL, CHECK (hourly_rate >= 0) |
| `lesson_fee` | NUMERIC(10,2) | NOT NULL, CHECK (lesson_fee >= 0) |
| `notes` | TEXT | Optional |

**Primary Key:** `lesson_id`  
**Foreign Key:** `student_id` → `students.student_id`

Each lesson belongs to one student and may cover one or more subjects. Preserve `hourly_rate` and the charged `lesson_fee` on the lesson itself so historic bills remain unchanged when prices change. Normally, `lesson_fee = ROUND(duration_minutes * hourly_rate / 60, 2)`; adjustments must be deliberate and documented.

### Payments

| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `payment_id` | BIGINT | PK, auto-generated |
| `student_id` | BIGINT | FK → students.student_id, NOT NULL |
| `payment_date` | DATE | NOT NULL |
| `amount` | NUMERIC(10,2) | NOT NULL, CHECK (amount > 0) |
| `payment_method` | VARCHAR(30) | `paynow` / `bank_transfer` / `cash` / `other`; optional |
| `reference` | VARCHAR(150) | Optional transaction reference |
| `notes` | TEXT | Optional |

**Primary Key:** `payment_id`  
**Foreign Key:** `student_id` → `students.student_id`

A payment records money actually received against one student's tuition account. One payment can settle multiple lessons, and a lesson can be settled by multiple partial payments.

### Expenses

| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `expense_id` | BIGINT | PK, auto-generated |
| `lesson_id` | BIGINT | FK → lessons.lesson_id, NOT NULL |
| `expense_date` | DATE | NOT NULL |
| `category` | VARCHAR(50) | NOT NULL; `transport` / `materials` / `other` |
| `description` | TEXT | Optional |
| `amount` | NUMERIC(10,2) | NOT NULL, CHECK (amount >= 0) |

**Primary Key:** `expense_id`  
**Foreign Key:** `lesson_id` → `lessons.lesson_id`

Each expense belongs to one lesson, and a lesson may incur multiple expenses. General expenses not attributable to lessons would require making `lesson_id` optional or adding a separate category later.

---

## Associative Tables

### student_subjects
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `student_id` | BIGINT | PK, FK → students.student_id |
| `subject_id` | BIGINT | PK, FK → subjects.subject_id |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'active'; `active` / `completed` / `paused` |

**Composite Primary Key:** (`student_id`, `subject_id`)

### question_topics
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `question_id` | BIGINT | PK, FK → questions.question_id |
| `topic_id` | BIGINT | PK, FK → topics.topic_id |

**Composite Primary Key:** (`question_id`, `topic_id`)

### question_chapters
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `question_id` | BIGINT | PK, FK → questions.question_id |
| `chapter_id` | BIGINT | PK, FK → chapters.chapter_id |

**Composite Primary Key:** (`question_id`, `chapter_id`)

### question_skills
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `question_id` | BIGINT | PK, FK → questions.question_id |
| `skill_id` | BIGINT | PK, FK → skills.skill_id |

**Composite Primary Key:** (`question_id`, `skill_id`)

### assessment_questions
| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `assessment_question_id` | BIGINT | PK, auto-generated |
| `assessment_id` | BIGINT | FK → assessments.assessment_id, NOT NULL |
| `question_id` | BIGINT | FK → questions.question_id, NOT NULL |
| `sequence_number` | INTEGER | Optional, CHECK (sequence_number > 0) |
| `marks_possible` | NUMERIC(5,2) | Optional until configured, CHECK (marks_possible > 0) |
| `marks_awarded` | NUMERIC(5,2) | Optional until graded |
| `feedback` | TEXT | Optional |

**Primary Key:** `assessment_question_id`

**Foreign Keys:**

- `assessment_id` → `assessments.assessment_id`

- `question_id` → `questions.question_id`

**Unique Constraints:** `UNIQUE(assessment_id, sequence_number)` and `UNIQUE(assessment_id, question_id)`

**Check Constraints:**

- `CHECK(sequence_number > 0)`

- `CHECK(marks_possible > 0)`

- `CHECK(marks_awarded IS NULL OR marks_possible IS NOT NULL)`

- `CHECK(marks_awarded >= 0 AND marks_awarded <= marks_possible)`

Each record represents a particular question included once in an assessment.

It identifies the question, preserves its position in the assessment, and optionally stores the student's marks and feedback.

`marks_awarded = NULL` indicates that the question has not yet been graded.

The same question may appear in multiple assessments (including reattempts), but only once within a given assessment.

An assessment may contain questions from multiple resources.

**---**

### lesson_subjects

| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `lesson_id` | BIGINT | PK, FK → lessons.lesson_id |
| `subject_id` | BIGINT | PK, FK → subjects.subject_id |

**Composite Primary Key:** (`lesson_id`, `subject_id`)

A lesson can cover multiple subjects; a subject can be covered in multiple lessons. A completed lesson should cover at least one subject. Any subject assigned to a lesson must also belong to that lesson's student's tuition enrollment (`student_subjects`).

### payment_allocations

| Attribute | Data Type | Constraints / Notes |
|---|---|---|
| `payment_id` | BIGINT | PK, FK → payments.payment_id |
| `lesson_id` | BIGINT | PK, FK → lessons.lesson_id |
| `allocated_amount` | NUMERIC(10,2) | NOT NULL, CHECK (allocated_amount > 0) |

**Composite Primary Key:** (`payment_id`, `lesson_id`)

An allocation applies some or all of a payment to a lesson's charge. Allocations must reference a payment and lesson belonging to the same student. Unallocated portions of a payment remain credit on the student's account.

---

## Relational Schema Summary

| Table | Primary Key | Foreign Keys |
|---|---|---|
| `students` | `student_id` | — |
| `subjects` | `subject_id` | — |
| `topics` | `topic_id` | `subject_id` |
| `chapters` | `chapter_id` | `topic_id` |
| `resources` | `resource_id` | `subject_id` |
| `questions` | `question_id` | `resource_id`, `format_id` |
| `question_formats` | `format_id` | — |
| `skills` | `skill_id` | — |
| `assessments` | `assessment_id` | `student_id` |
| `lessons` | `lesson_id` | `student_id` |
| `payments` | `payment_id` | `student_id` |
| `expenses` | `expense_id` | `lesson_id` |
| `student_subjects` | (`student_id`, `subject_id`) | `student_id`, `subject_id` |
| `question_topics` | (`question_id`, `topic_id`) | `question_id`, `topic_id` |
| `question_chapters` | (`question_id`, `chapter_id`) | `question_id`, `chapter_id` |
| `question_skills` | (`question_id`, `skill_id`) | `question_id`, `skill_id` |
| `assessment_questions` | `assessment_question_id` | `assessment_id`, `question_id` |
| `lesson_subjects` | (`lesson_id`, `subject_id`) | `lesson_id`, `subject_id` |
| `payment_allocations` | (`payment_id`, `lesson_id`) | `payment_id`, `lesson_id` |

**Total: 19 tables (12 main/operational tables + 7 associative tables).**

---

## Business Rules and Constraints

### Curriculum and Students

1. A subject is uniquely identified by `(name, academic_level, curriculum)`.
2. A student must study at least one subject, and a subject may have zero or more students; each `(student_id, subject_id)` enrollment pair is unique.
3. Every topic belongs to exactly one subject. A fully populated subject must have at least one topic.
4. Every chapter belongs to exactly one topic. A fully populated topic must have at least one chapter.
5. Topic names must be unique within a subject, and chapter names must be unique within a topic.

### Resources and Question Classification

6. Every resource belongs to exactly one subject; an unprocessed resource may contain zero questions.
7. Every question belongs to exactly one resource and must have a question number. Question numbers are unique within resource and section (a missing section counts as one section).
8. Question marks must be nonnegative, and page numbers, when present, must be positive.
9. Resource status is one of `uploaded`, `processing`, `review_required`, `completed`, or `failed`.
10. Questions may be temporarily unclassified. A fully classified question must have at least one topic or chapter association.
11. Questions may reference multiple topics and chapters, but those must belong to the question's resource's subject.
12. Each question has zero or one primary response format, and a format can apply to many questions.
13. Each question may assess zero or more skills; skills may be used across different subjects and chapters.
14. Topic, chapter, and skill associations are separately managed through `question_topics`, `question_chapters`, and `question_skills`.

### Assessments

15. Every assessment belongs to exactly one student, and a student may have zero or more assessments.
16. An assessment's type describes its purpose; `source_type` describes how its questions were assembled, not a strict single-resource foreign key.
17. Assessment `status` is `draft`, `assigned`, `submitted`, or `graded`. Draft assessments may be empty; other statuses require at least one question.
18. Assessments contain questions from one or many resources through `assessment_questions`; each included question references an existing library question.
19. Within one assessment, each `question_id` is included at most once; its `sequence_number`, if set, must be unique and positive.
20. Separate assessment records represent reattempts of the same question set.
21. `marks_possible` is positive when given. `marks_awarded` may be NULL before grading, but if provided it must be between zero and `marks_possible` inclusive.
22. `marks_awarded = NULL` means ungraded, not zero. An assessment is Graded only when every included question has a configured maximum and a recorded mark.
23. Assessment totals are derived from question-level records, and results can be analyzed by topic, chapter, skill, format, and difficulty.

### Lessons and Financial Records

24. Each lesson belongs to exactly one student; a student may have zero or many lessons.
25. A lesson may cover multiple subjects, and a subject may be taught in many lessons. A completed lesson must cover at least one subject enrolled by that student.
26. Lesson duration must be positive, hourly rate and lesson fee nonnegative, and each lesson retains its historical rate and charged fee.
27. Each payment belongs to exactly one student's tuition account, with a positive amount and a recorded payment date.
28. A payment may be allocated to multiple lessons, and a lesson may receive allocations from multiple payments. Both may have zero allocations initially.
29. Payment allocations must involve lessons and payments belonging to the same student.
30. The sum of allocations from a payment must not exceed the payment amount; the sum allocated to a lesson must not exceed its fee.
31. Any unallocated payment balance represents student credit. Lesson outstanding balance equals `lesson_fee - SUM(allocated_amount)`.
32. Lesson payment status (unpaid, partially paid, paid) is calculated rather than stored independently.
33. Each expense belongs to exactly one lesson, and a lesson may have zero or many expenses. Expense amounts must be nonnegative.
34. Cash received, billed tuition, outstanding fees, and expenses are distinct totals and should not be conflated. Net cash flow for a period is payment receipts minus recorded expenses in that period.

### Data Integrity

35. Primary keys are unique and non-null, and foreign keys refer to existing records.
36. Prevent unintended cascading deletion of students, resources, assessed questions, lessons, payments, and historical financial data.
37. Rules involving sums, related student identities, or the existence of child records need transactional application logic and/or database triggers; ordinary row-level `CHECK` constraints are insufficient.

---

## Implementation Notes

### PostgreSQL Keys and Constraints

- Use `BIGINT GENERATED ALWAYS AS IDENTITY` for auto-generated identifiers.
- Include FK columns physically in child tables even if the conceptual Chen diagram represents the relationships using diamonds.
- Enforce `NOT NULL` on required foreign keys and attributes; use composite primary keys for `student_subjects`, `question_topics`, `question_chapters`, `question_skills`, `lesson_subjects`, and `payment_allocations`.
- Keep the surrogate `assessment_question_id` PK, with `UNIQUE(assessment_id, question_id)` because the current conceptual M:N model permits only one occurrence of a given question per assessment.
- Enforce `UNIQUE(assessment_id, sequence_number)` on populated question positions.
- Apply uniqueness to `subjects(name, academic_level, curriculum)`, `topics(subject_id, name)`, `chapters(topic_id, name)`, `question_formats(name)`, `skills(name)`, and `questions(resource_id, section, question_number)`.
- Since `section` is optional, the `questions` uniqueness rule uses `UNIQUE NULLS NOT DISTINCT` (PostgreSQL 15+) so duplicate question numbers are also rejected when section is NULL. `question_number` is NOT NULL so that unnumbered questions do not collide with each other.
- Status, type, and category columns use `CHECK` constraints with lowercase snake_case values (e.g. `review_required`, `bank_transfer`), matching their defaults. Status columns are NOT NULL with a default (`resources.status = 'uploaded'`, `questions.classification_status = 'unclassified'`, `assessments.status = 'draft'`, `student_subjects.status = 'active'`). PostgreSQL enum types or lookup tables are alternatives.
- Index foreign key columns not already covered by a primary key or unique constraint, since PostgreSQL does not create these automatically.

### Assessment Processing

- Store `assessments.status` with default `draft`. Define valid transitions among `draft`, `assigned`, `submitted`, and `graded` in application logic.
- Allow draft assessments to have zero questions. Validate that assigned/submitted/graded assessments contain at least one.
- In `assessment_questions`, use `CHECK (marks_possible > 0)`, `CHECK (marks_awarded IS NULL OR marks_possible IS NOT NULL)`, and `CHECK (marks_awarded >= 0 AND marks_awarded <= marks_possible)`.
- Do not treat NULL marks as zero. Consider an assessment graded only when all included questions have `marks_possible` and `marks_awarded`.
- Use `questions.marks` as a default reference; store `marks_possible` on each assessment-question record to preserve historical marking schemes.
- Retrieve resource origins through `assessment_questions → questions → resources`. A mixed-source assessment does not need its own `resource_id`.
- Derive assessment totals and category performance through joins. Multi-tagged questions may contribute to more than one topic/skill category; avoid accidental double-counting in overall totals.
- Question files for custom assessments must still have a resource record under the current schema.
- A conceptual M:N `contains` diamond maps to the physical `assessment_questions` table. If repeating the *same* question within *one* assessment becomes necessary, remove the `(assessment_id, question_id)` uniqueness rule and revisit the conceptual ER model.

### Lessons, Payments, and Expenses

- Store `duration_minutes`, `hourly_rate`, and the final charged `lesson_fee` for each lesson. Calculate normal charges using decimal arithmetic and a consistent two-decimal rounding policy. Preserve any deliberate adjustments.
- Store the student's identity on both lessons and payments, allowing quick tuition-account queries. Validate that `payment_allocations` only joins matching student accounts.
- A payment may be partially allocated or temporarily unallocated. Do not force its total allocations to equal its amount.
- Enforce allocation sum limits and cross-table student consistency inside transactions with locking or database triggers to avoid concurrent over-allocation.
- Derive outstanding balances as lesson fees minus allocations; don't add a separate paid/unpaid column to lessons.
- Use `NUMERIC(10,2)` rather than floating-point money amounts. Use dates to report cash received (`payments.payment_date`) separately from billed income (`lessons.lesson_date`).
- Use `lesson_subjects` to support lessons with multiple subjects; validate that those subjects match the student's enrolled subjects. Multiple subjects do not imply multiple lesson fees unless separate pricing is later introduced.
- Associate expenses with lessons via `lesson_id`. Revenue and expenses should not be netted directly into individual payment records.
- For reporting, distinguish outstanding lesson charges from unallocated student credits; the student's net account balance can account for both.

### Resource Integrity and Operations

- Allow question format, topic, chapter, and skill classification to remain incomplete during ingestion, but validate classification when records are marked complete.
- Ensure assigned topics and chapters match the subject of the parent resource using transaction-based validation or triggers.
- Preserve uploaded PDFs and extracted question images in storage; keep only storage paths and metadata in PostgreSQL.
- Use `ON DELETE RESTRICT` for referenced historical records and `CASCADE` only for associations safe to discard:
  - `CASCADE`: `student_subjects` (from student), `question_topics` / `question_chapters` / `question_skills` (from question), `assessment_questions` (from assessment), `lesson_subjects` (from lesson).
  - `SET NULL`: `questions.format_id` when a question format is deleted.
  - `RESTRICT`: everything else, including all financial tables (`lessons`, `payments`, `expenses`, `payment_allocations`) and questions referenced by assessments.
- Use database transactions for uploads, assessment creation, lesson recording, payment allocation, and grading.
- Avoid committing real minors' personal information, financial records, or storage credentials to a public repository. Use synthetic test data and restricted storage access.
- Maintain lowercase snake_case for SQL objects and use pytest for FK, uniqueness, classification, grading, and payment-allocation edge cases.