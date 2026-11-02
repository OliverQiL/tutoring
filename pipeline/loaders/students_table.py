"""
CREATE TABLE students (
    student_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    school          VARCHAR(150),
    academic_level  VARCHAR(50)  NOT NULL,
    curriculum      VARCHAR(100) NOT NULL,
    CONSTRAINT uq_students_full_name UNIQUE (full_name)
);
"""

import pandas as pd
from pipeline import db
from pipeline import cleaning

DATA_FILE_PATH = "data/raw/tutoring_data.xlsx"
SHEET_NAME = "Students"

def load_students_table(conn, data_file_path=DATA_FILE_PATH, sheet_name=SHEET_NAME):
    # read the students data from the Excel file
    students_data = pd.read_excel(data_file_path, sheet_name=sheet_name, dtype=str, engine="calamine")

    # cleaning students_data
    # drop columns 'age' and 'subjects studying' (subjects studying is a separate table)
    students_data = students_data[["first name", "last name", "current school", "academic level", "curriculum"]]

    # clean the data using the clean_data function from pipeline/cleaning.py
    # strips, lowercases, drops NaN rows, and drops duplicates
    students_data = cleaning.clean_data(students_data)

    # combine first and last names into full name using full_name function from pipeline/cleaning.py
    students_data["full_name"] = students_data.apply(lambda row: cleaning.full_name(row["first name"], row["last name"]), axis=1)

    # drop the original first name and last name columns
    students_data = students_data[["full_name", "current school", "academic level", "curriculum"]]

    # convert dataframe rows into a list of tuples
    tuple_list = list(students_data.itertuples(index=False, name=None))

    with conn.cursor() as cur:
        # count the number of rows in the students table before inserting new data
        cur.execute("SELECT COUNT(*) FROM students;")
        before_count = cur.fetchone()[0]

        # insert data into the students table (%s are placeholders)
        insert_query = """
            INSERT INTO students (full_name, school, academic_level, curriculum)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (full_name) DO UPDATE
            SET school = EXCLUDED.school,
                academic_level = EXCLUDED.academic_level,
                curriculum = EXCLUDED.curriculum;
        """
        cur.executemany(insert_query, tuple_list)

        # count the number of rows in the students table after inserting new data
        cur.execute("SELECT COUNT(*) FROM students;")
        after_count = cur.fetchone()[0]

        # number of rows inserted is the difference between after_count and before_count
        rows_inserted = after_count - before_count
        skipped_rows = len(tuple_list) - rows_inserted

        return rows_inserted, skipped_rows

if __name__ == "__main__":
    # create a connection to the database
    with db.connect_to_db() as conn:
        # load the students table
        rows_inserted, skipped_rows = load_students_table(conn)
        print(f"Inserted {rows_inserted} new rows into the students table.")
        print(f"Skipped {skipped_rows} rows due to duplicates already in DB.")

