import pandas as pd
from pipeline import db

DATA_FILE_PATH = "data/raw/tutoring_data.xlsx"
SHEET_NAME = "Subjects Info"

def load_subjects_table(conn, data_file_path=DATA_FILE_PATH, sheet_name=SHEET_NAME):
    # read the subjects data from the Excel file
    subjects_data = pd.read_excel(data_file_path, sheet_name=sheet_name, dtype=str)

    # cleaning subjects_data
    # drop columns 'topics' and 'chapters'
    # instead of using drop(), we specify the columns to keep and the order we want them in
    # this way, we can ensure that the columns are in the correct order for insertion into the database
    subjects_data = subjects_data[["curriculum", "academic level", "subjects"]]

    # drop rows where all elements are NaN
    subjects_data = subjects_data.dropna(how="all") 

    # strip whitespace from every value of every column, then lowercase everything
    for column in subjects_data.columns:
        subjects_data[column] = subjects_data[column].str.strip()
        subjects_data[column] = subjects_data[column].str.lower()

    # drop duplicates
    subjects_data = subjects_data.drop_duplicates()

    # convert dataframe rows into a list of tuples
    # order is ensured by the previous step where we specified the columns to keep and their order
    tuple_list = list(subjects_data.itertuples(index=False, name=None))

    # now we can use this list of tuples to insert data into the database
    # we already have a connection to the database, so we can use it to execute the insert query
    with conn.cursor() as cur:
        # count the number of rows in the subjects table before inserting new data
        cur.execute("SELECT COUNT(*) FROM subjects;")
        before_count = cur.fetchone()[0]

        # insert data into the subjects table (%s are placeholders)
        # order is ensured by the previous steps where we specified the columns to keep and their order
        insert_query = """
            INSERT INTO subjects (curriculum, academic_level, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (curriculum, academic_level, name) DO NOTHING;
        """
        # executemany() is used to execute the same query for multiple sets of tuples
        cur.executemany(insert_query, tuple_list)

        # count the number of rows in the subjects table after inserting new data
        cur.execute("SELECT COUNT(*) FROM subjects;")
        after_count = cur.fetchone()[0]

        # number of rows inserted is the difference between after_count and before_count
        rows_inserted = after_count - before_count
        skipped_rows = len(tuple_list) - rows_inserted

        return rows_inserted, skipped_rows

if __name__ == "__main__":
    # create a connection to the database
    with db.connect_to_db() as conn:

        # load the subjects table
        rows_inserted, skipped_rows = load_subjects_table(conn)
        print(f"Inserted {rows_inserted} new rows into the subjects table.")
        print(f"Skipped {skipped_rows} rows due to duplicates already in DB.")