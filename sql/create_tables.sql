-- =============================================================================
-- Tuition Management Platform: schema creation script
-- Target: PostgreSQL 15+ (uses UNIQUE NULLS NOT DISTINCT)
--
-- Creates 19 tables (12 main + 7 associative) as specified in README.md.
-- Status / category values are stored as lowercase snake_case strings.
--
-- Rules NOT enforced here (need triggers or transactional application logic):
--   - topics/chapters tagged on a question belong to the resource's subject
--   - lesson_subjects only reference subjects the student is enrolled in
--   - payment_allocations join a payment and lesson of the same student
--   - SUM(allocated_amount) <= payment amount and <= lesson fee
--   - non-draft assessments contain at least one question
--   - "at least one child" rules (student has a subject, lesson has a subject, ...)
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Curriculum
-- -----------------------------------------------------------------------------

CREATE TABLE students (
    student_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    school          VARCHAR(150),
    academic_level  VARCHAR(50)  NOT NULL,
    curriculum      VARCHAR(100) NOT NULL
);

CREATE TABLE subjects (
    subject_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    academic_level  VARCHAR(50)  NOT NULL,
    curriculum      VARCHAR(100) NOT NULL,
    description     TEXT,
    CONSTRAINT uq_subjects_name_level_curriculum UNIQUE (name, academic_level, curriculum)
);

CREATE TABLE topics (
    topic_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subject_id      BIGINT       NOT NULL REFERENCES subjects (subject_id) ON DELETE RESTRICT,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    CONSTRAINT uq_topics_subject_name UNIQUE (subject_id, name)
);

CREATE TABLE chapters (
    chapter_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    topic_id        BIGINT       NOT NULL REFERENCES topics (topic_id) ON DELETE RESTRICT,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    CONSTRAINT uq_chapters_topic_name UNIQUE (topic_id, name)
);

-- -----------------------------------------------------------------------------
-- Resources and questions
-- -----------------------------------------------------------------------------

CREATE TABLE resources (
    resource_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subject_id       BIGINT       NOT NULL REFERENCES subjects (subject_id) ON DELETE RESTRICT,
    title            VARCHAR(255) NOT NULL,
    resource_type    VARCHAR(30),
    publication_year INTEGER,
    file_path        TEXT         NOT NULL,
    file_type        VARCHAR(20),
    status           VARCHAR(30)  NOT NULL DEFAULT 'uploaded',
    uploaded_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_resources_resource_type
        CHECK (resource_type IN ('exam', 'worksheet', 'exercise')),
    CONSTRAINT ck_resources_file_type
        CHECK (file_type IN ('pdf', 'png', 'jpeg')),
    CONSTRAINT ck_resources_status
        CHECK (status IN ('uploaded', 'processing', 'review_required', 'completed', 'failed'))
);

CREATE TABLE question_formats (
    format_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    CONSTRAINT uq_question_formats_name UNIQUE (name)
);

CREATE TABLE skills (
    skill_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    CONSTRAINT uq_skills_name UNIQUE (name)
);

CREATE TABLE questions (
    question_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_id           BIGINT       NOT NULL REFERENCES resources (resource_id) ON DELETE RESTRICT,
    format_id             BIGINT       REFERENCES question_formats (format_id) ON DELETE SET NULL,
    question_number       VARCHAR(30)  NOT NULL,
    section               VARCHAR(20),
    question_text         TEXT,
    marks                 NUMERIC(5,2),
    difficulty            VARCHAR(20),
    page_number           INTEGER,
    image_path            TEXT,
    classification_status VARCHAR(30)  NOT NULL DEFAULT 'unclassified',
    CONSTRAINT uq_questions_resource_section_number
        UNIQUE NULLS NOT DISTINCT (resource_id, section, question_number),
    CONSTRAINT ck_questions_marks
        CHECK (marks >= 0),
    CONSTRAINT ck_questions_page_number
        CHECK (page_number > 0),
    CONSTRAINT ck_questions_difficulty
        CHECK (difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT ck_questions_classification_status
        CHECK (classification_status IN ('unclassified', 'review_required', 'classified'))
);

-- -----------------------------------------------------------------------------
-- Assessments
-- -----------------------------------------------------------------------------

CREATE TABLE assessments (
    assessment_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id      BIGINT       NOT NULL REFERENCES students (student_id) ON DELETE RESTRICT,
    title           VARCHAR(255) NOT NULL,
    assessment_date DATE,
    assessment_type VARCHAR(30),
    status          VARCHAR(20)  NOT NULL DEFAULT 'draft',
    source_type     VARCHAR(30),
    notes           TEXT,
    CONSTRAINT ck_assessments_assessment_type
        CHECK (assessment_type IN ('exam', 'test', 'homework', 'practice', 'diagnostic')),
    CONSTRAINT ck_assessments_status
        CHECK (status IN ('draft', 'assigned', 'submitted', 'graded')),
    CONSTRAINT ck_assessments_source_type
        CHECK (source_type IN ('full_resource', 'selected_questions', 'mixed_resources', 'original'))
);

-- -----------------------------------------------------------------------------
-- Lessons and financial records
-- -----------------------------------------------------------------------------

CREATE TABLE lessons (
    lesson_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id       BIGINT        NOT NULL REFERENCES students (student_id) ON DELETE RESTRICT,
    lesson_date      DATE          NOT NULL,
    duration_minutes INTEGER       NOT NULL,
    hourly_rate      NUMERIC(10,2) NOT NULL,
    lesson_fee       NUMERIC(10,2) NOT NULL,
    notes            TEXT,
    CONSTRAINT ck_lessons_duration_minutes CHECK (duration_minutes > 0),
    CONSTRAINT ck_lessons_hourly_rate      CHECK (hourly_rate >= 0),
    CONSTRAINT ck_lessons_lesson_fee       CHECK (lesson_fee >= 0)
);

CREATE TABLE payments (
    payment_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id      BIGINT        NOT NULL REFERENCES students (student_id) ON DELETE RESTRICT,
    payment_date    DATE          NOT NULL,
    amount          NUMERIC(10,2) NOT NULL,
    payment_method  VARCHAR(30),
    reference       VARCHAR(150),
    notes           TEXT,
    CONSTRAINT ck_payments_amount
        CHECK (amount > 0),
    CONSTRAINT ck_payments_payment_method
        CHECK (payment_method IN ('paynow', 'bank_transfer', 'cash', 'other'))
);

CREATE TABLE expenses (
    expense_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lesson_id       BIGINT        NOT NULL REFERENCES lessons (lesson_id) ON DELETE RESTRICT,
    expense_date    DATE          NOT NULL,
    category        VARCHAR(50)   NOT NULL,
    description     TEXT,
    amount          NUMERIC(10,2) NOT NULL,
    CONSTRAINT ck_expenses_category
        CHECK (category IN ('transport', 'materials', 'other')),
    CONSTRAINT ck_expenses_amount
        CHECK (amount >= 0)
);

-- -----------------------------------------------------------------------------
-- Associative tables
-- -----------------------------------------------------------------------------

CREATE TABLE student_subjects (
    student_id      BIGINT      NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    subject_id      BIGINT      NOT NULL REFERENCES subjects (subject_id) ON DELETE RESTRICT,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    PRIMARY KEY (student_id, subject_id),
    CONSTRAINT ck_student_subjects_status
        CHECK (status IN ('active', 'completed', 'paused'))
);

CREATE TABLE question_topics (
    question_id     BIGINT NOT NULL REFERENCES questions (question_id) ON DELETE CASCADE,
    topic_id        BIGINT NOT NULL REFERENCES topics (topic_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, topic_id)
);

CREATE TABLE question_chapters (
    question_id     BIGINT NOT NULL REFERENCES questions (question_id) ON DELETE CASCADE,
    chapter_id      BIGINT NOT NULL REFERENCES chapters (chapter_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, chapter_id)
);

CREATE TABLE question_skills (
    question_id     BIGINT NOT NULL REFERENCES questions (question_id) ON DELETE CASCADE,
    skill_id        BIGINT NOT NULL REFERENCES skills (skill_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, skill_id)
);

CREATE TABLE assessment_questions (
    assessment_question_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    assessment_id          BIGINT       NOT NULL REFERENCES assessments (assessment_id) ON DELETE CASCADE,
    question_id            BIGINT       NOT NULL REFERENCES questions (question_id) ON DELETE RESTRICT,
    sequence_number        INTEGER,
    marks_possible         NUMERIC(5,2),
    marks_awarded          NUMERIC(5,2),
    feedback               TEXT,
    CONSTRAINT uq_assessment_questions_assessment_question
        UNIQUE (assessment_id, question_id),
    CONSTRAINT uq_assessment_questions_assessment_sequence
        UNIQUE (assessment_id, sequence_number),
    CONSTRAINT ck_assessment_questions_sequence_number
        CHECK (sequence_number > 0),
    CONSTRAINT ck_assessment_questions_marks_possible
        CHECK (marks_possible > 0),
    CONSTRAINT ck_assessment_questions_awarded_requires_possible
        CHECK (marks_awarded IS NULL OR marks_possible IS NOT NULL),
    CONSTRAINT ck_assessment_questions_marks_awarded_range
        CHECK (marks_awarded >= 0 AND marks_awarded <= marks_possible)
);

CREATE TABLE lesson_subjects (
    lesson_id       BIGINT NOT NULL REFERENCES lessons (lesson_id) ON DELETE CASCADE,
    subject_id      BIGINT NOT NULL REFERENCES subjects (subject_id) ON DELETE RESTRICT,
    PRIMARY KEY (lesson_id, subject_id)
);

CREATE TABLE payment_allocations (
    payment_id       BIGINT        NOT NULL REFERENCES payments (payment_id) ON DELETE RESTRICT,
    lesson_id        BIGINT        NOT NULL REFERENCES lessons (lesson_id) ON DELETE RESTRICT,
    allocated_amount NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (payment_id, lesson_id),
    CONSTRAINT ck_payment_allocations_allocated_amount
        CHECK (allocated_amount > 0)
);

-- -----------------------------------------------------------------------------
-- Indexes on foreign keys (PostgreSQL does not create these automatically).
-- The leading column of each composite PK / unique constraint is already indexed.
-- -----------------------------------------------------------------------------

CREATE INDEX ix_resources_subject_id           ON resources (subject_id);
CREATE INDEX ix_questions_format_id            ON questions (format_id);
CREATE INDEX ix_assessments_student_id         ON assessments (student_id);
CREATE INDEX ix_lessons_student_id_date        ON lessons (student_id, lesson_date);
CREATE INDEX ix_payments_student_id_date       ON payments (student_id, payment_date);
CREATE INDEX ix_expenses_lesson_id             ON expenses (lesson_id);
CREATE INDEX ix_student_subjects_subject_id    ON student_subjects (subject_id);
CREATE INDEX ix_question_topics_topic_id       ON question_topics (topic_id);
CREATE INDEX ix_question_chapters_chapter_id   ON question_chapters (chapter_id);
CREATE INDEX ix_question_skills_skill_id       ON question_skills (skill_id);
CREATE INDEX ix_assessment_questions_question  ON assessment_questions (question_id);
CREATE INDEX ix_lesson_subjects_subject_id     ON lesson_subjects (subject_id);
CREATE INDEX ix_payment_allocations_lesson_id  ON payment_allocations (lesson_id);

COMMIT;
