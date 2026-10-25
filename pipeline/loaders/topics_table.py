import pandas as pd
from pipeline import db
from pipeline import cleaning

DATA_FILE_PATH = "data/raw/tutoring_data.xlsx"
SHEET_NAME = "Subjects Info"

def load_topics_table(conn, data_file_path=DATA_FILE_PATH, sheet_name=SHEET_NAME):
    # read the topics data from the Excel file
    topics_data = pd.read_excel(data_file_path, sheet_name=sheet_name, dtype=str, engine="calamine")

    # cleaning topics_data
    # drop column 'chapter'
    # instead of using drop(), we specify the columns to keep and the order we want them in
    # this way, we can ensure that the columns are in the correct order for insertion into the database
    topics_data = topics_data[["curriculum", "academic level", "subjects", "topics"]]

    # clean the data using the clean_data function from pipeline/cleaning.py
    # strips, lowercases, drops NaN rows, and drops duplicates
    topics_data = cleaning.clean_data(topics_data)

    # convert dataframe rows into a list of tuples
    # order is ensured by the previous step where we specified the columns to keep and their order
    tuple_list = list(topics_data.itertuples(index=False, name=None))

    # now we can use this list of tuples to insert data into the database
    # we already have a connection to the database, so we can use it to execute the insert query
    with conn.cursor() as cur:
        # first we build a lookup dictionary to map the curriculum, academic level, and name to the subject_id
        cur.execute("SELECT subject_id, curriculum, academic_level, name FROM subjects;")

        result = cur.fetchall() # a list of tuples (id, curriculum, academic_level, name)

        # convert list of tuples to dictionary (key is a tuple of (curriculum, academic_level, name), value is subject_id)
        subject_dict = {(row[1], row[2], row[3]): row[0] for row in result}

        # now we can use this dictionary to get the subject_id for each row in topics_data
        # we will create a new list of tuples that includes the subject_id
        topics_with_subject_id = []
        topics_skipped = []
        for row in tuple_list:
            curriculum, academic_level, subject_name, topic_name = row
            subject_id = subject_dict.get((curriculum, academic_level, subject_name))
            if subject_id is not None:
                topics_with_subject_id.append((subject_id, topic_name))
            else:
                topics_skipped.append((curriculum, academic_level, subject_name, topic_name))
                print(f"Warning: No subject_id found for {curriculum}, {academic_level}, {subject_name}. Skipping this row.")

        # count the number of rows in the topics table before inserting new data
        cur.execute("SELECT COUNT(*) FROM topics;")
        before_count = cur.fetchone()[0]

        # insert data into the topics table (%s are placeholders)
        insert_query = """
            INSERT INTO topics (subject_id, name)
            VALUES (%s, %s)
            ON CONFLICT (subject_id, name) DO NOTHING;
        """
        # executemany() is used to execute the same query for multiple sets of tuples
        cur.executemany(insert_query, topics_with_subject_id)

        # count the number of rows in the topics table after inserting new data
        cur.execute("SELECT COUNT(*) FROM topics;")
        after_count = cur.fetchone()[0]

        # number of rows inserted is the difference between after_count and before_count
        rows_inserted = after_count - before_count
        skipped_rows = len(topics_with_subject_id) - rows_inserted + len(topics_skipped)

        return rows_inserted, skipped_rows, topics_skipped


if __name__ == "__main__":
    # create a connection to the database
    with db.connect_to_db() as conn:
        # load the topics table
        rows_inserted, skipped_rows, topics_skipped = load_topics_table(conn)
        print(f"Inserted {rows_inserted} new rows into the topics table.")
        print(f"Skipped {skipped_rows} rows due to duplicates already in DB or missing subject_id.")
        if topics_skipped:
            print("The following rows were skipped due to missing subject_id:")
            for skipped in topics_skipped:
                print(skipped)