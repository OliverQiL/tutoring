"""
CREATE TABLE student_subjects (
    student_id      BIGINT      NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    subject_id      BIGINT      NOT NULL REFERENCES subjects (subject_id) ON DELETE RESTRICT,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    PRIMARY KEY (student_id, subject_id),
    CONSTRAINT ck_student_subjects_status
        CHECK (status IN ('active', 'completed', 'paused'))
);
"""

import pandas as pd
from pipeline import db
from pipeline import cleaning

DATA_FILE_PATH = "data/raw/tutoring_data.xlsx"
SHEET_NAME = "Students"

def load_student_subjects_table(conn, data_file_path=DATA_FILE_PATH, sheet_name=SHEET_NAME):
    # read the students data from the Excel file
    students_data = pd.read_excel(data_file_path, sheet_name=sheet_name, dtype=str, engine="calamine")

    # cleaning students_data
    # need first name, last name, and subjects studying, plus curriculum and academic level
    # (subject names repeat across levels, so the student's curriculum and level are part of the subject key)
    students_data = students_data[["first name", "last name", "curriculum", "academic level", "subjects studying"]]

    # clean the data using the clean_data function from pipeline/cleaning.py
    # strips, lowercases, drops NaN rows, and drops duplicates
    students_data = cleaning.clean_data(students_data)

    # combine first and last names into full name using full_name function from pipeline/cleaning.py
    students_data["full_name"] = students_data.apply(lambda row: cleaning.full_name(row["first name"], row["last name"]), axis=1)

    # split subjects into a list using split_subjects function from pipeline/cleaning.py
    students_data["subjects_list"] = students_data["subjects studying"].apply(cleaning.split_subjects)

    # drop the original first name, last name, and subjects studying columns
    students_data = students_data[["full_name", "curriculum", "academic level", "subjects_list"]]

    # convert dataframe rows into a list of tuples (full_name, curriculum, academic_level, subject)
    tuple_list = []
    for _, row in students_data.iterrows():
        for subject in row["subjects_list"]:
            tuple_list.append((row["full_name"], row["curriculum"], row["academic level"], subject))

    with conn.cursor() as cur:
        # build a lookup dictionary to map the full_name to student_id
        cur.execute("SELECT student_id, full_name FROM students;")
        result = cur.fetchall()  # a list of tuples (student_id, full_name)
        student_lookup = {full_name: student_id for student_id, full_name in result}

        # build a lookup dictionary to map (curriculum, academic_level, name) to subject_id
        # the key must match the UNIQUE constraint on subjects: name alone repeats across levels
        cur.execute("SELECT subject_id, curriculum, academic_level, name FROM subjects;")
        result = cur.fetchall()  # a list of tuples (subject_id, curriculum, academic_level, name)
        subject_lookup = {(curriculum, level, name): subject_id for subject_id, curriculum, level, name in result}

        # now we can use these dictionaries to get the student_id and subject_id for each row in tuple_list
        student_subjects_with_ids = []
        skipped_missing_students = []
        skipped_missing_subjects = []
        for full_name, curriculum, level, subject in tuple_list:
            student_id = student_lookup.get(full_name)
            subject_id = subject_lookup.get((curriculum, level, subject))
            if student_id is not None and subject_id is not None:
                student_subjects_with_ids.append((student_id, subject_id))
            else:
                if student_id is None:
                    skipped_missing_students.append(full_name)
                    print(f"Warning: No student_id found for {full_name}. Skipping this row.")
                if subject_id is None:
                    skipped_missing_subjects.append((curriculum, level, subject))
                    print(f"Warning: No subject_id found for {curriculum}, {level}, {subject}. Skipping this row.")

        # count the number of rows in the student_subjects table before inserting new data
        cur.execute("SELECT COUNT(*) FROM student_subjects;")
        before_count = cur.fetchone()[0]

        # insert data into the student_subjects table (%s are placeholders)
        insert_query = """
            INSERT INTO student_subjects (student_id, subject_id)
            VALUES (%s, %s)
            ON CONFLICT (student_id, subject_id) DO NOTHING;
        """

        # executemany() is used to execute the same query for multiple sets of tuples
        cur.executemany(insert_query, student_subjects_with_ids)

        # count the number of rows in the student_subjects table after inserting new data
        cur.execute("SELECT COUNT(*) FROM student_subjects;")
        after_count = cur.fetchone()[0]

        # number of rows inserted is the difference between after_count and before_count
        rows_inserted = after_count - before_count
        skipped_rows = len(student_subjects_with_ids) - rows_inserted

        return rows_inserted, skipped_rows, skipped_missing_students, skipped_missing_subjects

if __name__ == "__main__":
    # create a connection to the database
    with db.connect_to_db() as conn:
        # load the student_subjects table
        rows_inserted, skipped_rows, skipped_missing_students, skipped_missing_subjects = load_student_subjects_table(conn)
        print(f"Inserted {rows_inserted} new rows into the student_subjects table.")
        print(f"Skipped {skipped_rows} rows due to duplicates already in DB or missing subject_id.")
        if skipped_missing_students:
            print("The following students were skipped due to missing student_id:")
            for student in skipped_missing_students:
                print(student)
        if skipped_missing_subjects:
            print("The following subjects were skipped due to missing subject_id:")
            for subject in skipped_missing_subjects:
                print(subject)
