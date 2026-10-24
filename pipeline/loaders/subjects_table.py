import pandas as pd
from pipeline import db

DATA_FILE_PATH = "data/raw/tutoring_data.xlsx"
SHEET_NAME = "Subjects Info"

def load_subjects_table(conn, data_file_path=DATA_FILE_PATH, sheet_name=SHEET_NAME):
    # read the subjects data from the Excel file
    subjects_data = pd.read_excel(data_file_path, sheet_name=sheet_name, dtype=str)

    # cleaning subjects_data
    # drop columns 'topics' and 'chapters'
    subjects_data.drop(columns=["topics", "chapters"], inplace=True)

    # drop rows where all elements are NaN
    subjects_data.dropna(inplace=True, how="all") 

    # strip whitespace from every value of every column, then lowercase everything
    for column in subjects_data.columns:
        subjects_data[column] = subjects_data[column].str.strip()
        subjects_data[column] = subjects_data[column].str.lower()

    # drop duplicates
    subjects_data.drop_duplicates(inplace=True)

    # convert dataframe rows into a list of tuples
    tuple_list = list(subjects_data.itertuples(index=False, name=None))

    # now we can use this list of tuples to insert data into the database
    # we already have a connection to the database, so we can use it to execute the insert query
    with conn.cursor() as cur:

        # insert data into the subjects table (%s are placeholders)
        insert_query = """
            INSERT INTO subjects (curriculum, academic_level, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (curriculum, academic_level, name) DO NOTHING;
        """
        # executemany() is used to execute the same query for multiple sets of tuples
        cur.executemany(insert_query, tuple_list)

if __name__ == "__main__":
    # create a connection to the database
    with db.connect_to_db() as conn:

        # load the subjects table
        load_subjects_table(conn)