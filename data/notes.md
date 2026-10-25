# Data Profile: `data/raw/tutoring_data.xlsx`

Profiled with `scripts/profile_data.py` (all sheets read with `dtype=str`). No personal values are recorded here.

## Sheet → table mapping

| Sheet | Rows | Target table(s) | Load order |
|---|---|---|---|
| Subjects Info | 146 (143 data + 3 blank) | `subjects`, `topics`, `chapters` | 1 |
| Students | 3 | `students`, `student_subjects` | 2 |
| Lessons | 10 | `lessons`, `lesson_subjects`, `expenses` | 3 |
| Payments | 0 (headers only) | `payments`, `payment_allocations` | 4 |

`resources` / `questions` come from the PDF pipeline.

## Canonical values (decided in stage 2)

Applied by every loader **before** inserting or looking anything up, so values from different sheets match exactly.

| Field | Rule | Stored values |
|---|---|---|
| curriculum | strip + lowercase | `mainstream primary`, `igcse` |
| academic level | strip + lowercase, abbreviations kept | `p4`, `p6`, `s2` |
| subject name | strip + lowercase | `mathematics`, `science` |
| topic / chapter name | strip + lowercase (decided in stage 3) | e.g. `matter`, `potential energy (gpe, epe, cpe)` |

**Typos are fixed in the source workbook, not in code.** There is no alias map: the Excel file is kept correct, and the loaders assume it is. If a value doesn't match (e.g. a student's curriculum has no matching subject), the loaders skip and report the row, and the fix is made in the workbook.

## Column mappings

### Subjects Info (one row per chapter)
| Column | → | Notes |
|---|---|---|
| `curriculum` | `subjects.curriculum` | 2 values: `mainstream primary`, `IGCSE` → stored lowercase |
| `academic level` | `subjects.academic_level` | 3 values: `P4`, `P6`, `S2` → stored lowercase |
| `subjects` | `subjects.name` | 2 values: `mathematics`, `science` |
| `topics` | `topics.name` | 29 distinct, all lowercase |
| `chapters` | `chapters.name` | 143 distinct, mixed / title case |

The sheet gives 4 distinct subjects: (mainstream primary, P4, science), (mainstream primary, P6, science), (mainstream primary, P6, mathematics), (IGCSE, S2, mathematics).

### Students
| Column | → | Notes |
|---|---|---|
| `first name` + `last name` | `students.full_name` | Combine with a single space |
| `current school` | `students.school` | |
| `curriculum` | `students.curriculum` | |
| `academic level` | `students.academic_level` | |
| `age` | none | Not in schema (see gaps) |
| `subjects studying` | `student_subjects` | Comma-separated list → one row per subject, resolved to `subject_id` via (name, student's level, student's curriculum) |

### Lessons
| Column | → | Notes |
|---|---|---|
| `date` | `lessons.lesson_date` | Stored as Excel dates; reads as `'2026-10-06 00:00:00'` → keep date part only |
| `student` | `lessons.student_id` | Full name; resolve via students lookup |
| `duration (in hours)` | `lessons.duration_minutes` | Values `1`, `1.5`, `2` (hours) → × 60 |
| `rate` | `lessons.hourly_rate` | Whole numbers → `Decimal` |
| `fee` | `lessons.lesson_fee` | Whole numbers → `Decimal` |
| `expenses` | `expenses.amount` | Filled on 5/10 lessons, all `30`. Blank means **no expense row**, not a 0.00 expense |
| `expense description` | `expenses.category` (+ `expenses.description`) | Filled on exactly the same 5 lessons, all `transportation`. Map to category `transport`; keep the original text as `description` or leave it NULL |
| (lesson `date`) | `expenses.expense_date` | No separate expense date; use the lesson date |
| (lesson row) | `expenses.lesson_id` | The expense belongs to the lesson on the same row |

### Payments
| Column | → | Notes |
|---|---|---|
| `date` | `payments.payment_date` | |
| `student` | `payments.student_id` | Full name; resolve via students lookup |
| `amount ` | `payments.amount` | **Header has a trailing space** |
| `method` | `payments.payment_method` | Map to `paynow` / `bank_transfer` / `cash` / `other` |

## Gaps between data and schema

- **Lessons have no subject column**, so `lesson_subjects` can't come straight from the data.
  - Students with one subject: infer it from `student_subjects`.
  - The two-subject student has 3 lessons, which need a rule or manual input. Decide in stage 6.
- **No payments yet.** The Payments sheet is empty, so stage 7 needs synthetic test rows in `data/sample/`.
- **At most one expense per lesson.** Expenses are two columns on the Lessons sheet, so a lesson with two expenses (e.g. transport + materials) can't be entered. That's fine for now; switch to a separate Expenses sheet with a lesson reference if it comes up.
- **No expense date or explicit category.** The date is taken from the lesson, and the category is mapped from the free-text description.
- **`age` has no column in the schema.** Either drop it, or add something like `date_of_birth`, because a stored age goes stale. Avoid storing more personal data on minors than you need.
- **No descriptions** for subjects, topics or chapters. These stay NULL.
- **No payment method values** exist yet to check against the allowed list.

## Problems found

| # | Sheet | Problem | Fix (stage 4) |
|---|---|---|---|
| 1 | Students | `curriculum` typo `maintream primary` (Subjects Info has `mainstream primary`). As a result, **3 of the 4 enrolments don't match any subject.** | **Fixed in the source workbook** (stage 3) |
| 2 | Students | Trailing whitespace on one `last name` and one `current school` | `strip()` every text cell |
| 3 | Lessons | `student` matches full names exactly in only 4/10 rows, but in 10/10 after strip + lowercase (caused by problem 2) | Match on a normalised full name |
| 4 | Subjects Info | 3 fully blank rows (used as separators). They are also the cause of the 2 duplicate rows. | Drop all-blank rows before validating |
| 5 | Subjects Info | Trailing whitespace in topics `light`, `sets and venn diagrams` and chapter `visualising nets` | `strip()`. Otherwise `UNIQUE(subject_id, name)` treats `light` and `light ` as different topics |
| 6 | Subjects Info | Topics are lowercase, chapters are title/mixed case | **Decided:** strip + lowercase both (see Canonical values) |
| 7 | Lessons | `duration (in hours)` is a decimal number of hours; the schema stores whole minutes | Convert with `Decimal`, check the result is a whole number of minutes |
| 8 | Lessons | pandas guesses `rate` / `fee` as int and duration as float | Read as `str`, convert to `Decimal` |
| 9 | Payments | Header `amount ` has a trailing space | Strip column names on read |
| 10 | All | Category values are inconsistent in style: `IGCSE` uppercase vs `mainstream primary` lowercase; levels are abbreviations (`P4`, `S2`) | **Decided:** strip + lowercase, abbreviations kept (see Canonical values) |
| 11 | Lessons | `expense description` value `transportation` isn't an allowed category (`transport` / `materials` / `other`) | Map description text to a category; unknown text → `other`, keep the text in `description` |
| 12 | Lessons | pandas guesses `expenses` as float64 because blank cells become NaN | Read as `str`, convert non-blank values to `Decimal`, skip blanks |

## Checks that passed

- `fee == duration × rate` for all 10 lessons. No fee adjustments.
- No chapter name repeats within a subject, and no chapter appears under two topics.
- No partially blank rows in Subjects Info. Every non-blank row has all 5 columns.
- Expense amount and description are always filled together: no amount without a description, or the reverse.
- Lesson dates are in order. Two lessons share one date, which is fine (different lessons).
- After the curriculum typo is fixed, every student's (curriculum, level, subject) exists in Subjects Info.

## Design choices (for problems)
problem 10 - standardize all lower case, levels use abbreviations (p4, s2)

