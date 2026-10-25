import pandas as pd
from pipeline import db
from pipeline import cleaning

DATA_FILE_PATH = "data/raw/tutoring_data.xlsx"
SHEET_NAME = "Subjects Info"

def load_chapters_table(conn, data_file_path=DATA_FILE_PATH, sheet_name=SHEET_NAME):
    # read the chapters data from the Excel file
    chapters_data = pd.read_excel(data_file_path, sheet_name=sheet_name, dtype=str, engine="calamine")

    # cleaning chapters_data
    # drop no columns
    # instead of using drop(), we specify the columns to keep and the order we want them in
    # this way, we can ensure that the columns are in the correct order for insertion into the database
    chapters_data = chapters_data[["curriculum", "academic level", "subjects", "topics", "chapters"]]

    # clean the data using the clean_data function from pipeline/cleaning.py
    # strips, lowercases, drops NaN rows, and drops duplicates
    chapters_data = cleaning.clean_data(chapters_data)

    # convert dataframe rows into a list of tuples
    # order is ensured by the previous step where we specified the columns to keep and their order
    tuple_list = list(chapters_data.itertuples(index=False, name=None))

    # now we can use this list of tuples to insert data into the database
    # we already have a connection to the database, so we can use it to execute the insert query
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.curriculum, s.academic_level, s.name, t.name, t.topic_id FROM subjects s
            JOIN topics t
            ON s.subject_id = t.subject_id
            """
        )

        result = cur.fetchall()
        topic_dict = {(row[0], row[1], row[2], row[3]): row[4] for row in result}

        chapters_with_topic_id = []
        chapters_skipped = []
        for row in tuple_list:
            curriculum, academic_level, subject_name, topic_name, chapter_name = row
            topic_id = topic_dict.get((curriculum, academic_level, subject_name, topic_name))
            if topic_id is not None:
                chapters_with_topic_id.append((topic_id, chapter_name))
            else:
                chapters_skipped.append((curriculum, academic_level, subject_name, topic_name, chapter_name))

        cur.execute("SELECT COUNT(*) FROM chapters;")
        before_count = cur.fetchone()[0]

        insert_query = """
            INSERT INTO chapters (topic_id, name)
            VALUES (%s, %s)
            ON CONFLICT (topic_id, name) DO NOTHING;
        """

        cur.executemany(insert_query, chapters_with_topic_id)

        cur.execute("SELECT COUNT(*) FROM chapters;")
        after_count = cur.fetchone()[0]

        rows_inserted = after_count - before_count
        skipped_rows = len(chapters_with_topic_id) - rows_inserted + len(chapters_skipped)

        return rows_inserted, skipped_rows, chapters_skipped

if __name__ == "__main__":
    with db.connect_to_db() as conn:
        rows_inserted, skipped_rows, chapters_skipped = load_chapters_table(conn)
        print(f"Inserted {rows_inserted} new rows into the chapters table.")
        print(f"Skipped {skipped_rows} rows due to duplicates already in DB.")
        if chapters_skipped:
            print("The following rows were skipped because no matching topic_id was found:")
            for skipped in chapters_skipped:
                print(skipped)