import psycopg
from pipeline import config

def connect_to_db():
    """
    Connect to the PostgreSQL database using the connection string from the config file.
    Returns a connection object.
    """
    try:
        # connect to the database
        conn = psycopg.connect(config.get_env_variable("DATABASE_URL"))
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        raise

if __name__ == "__main__":
    # test the database connection
    with connect_to_db() as conn:
        with conn.cursor() as cur:

            # execute a simple query to test the connection
            cur.execute("SELECT version();")

            # fetchone(), fetchall(), and fetchmany() are methods to retrieve query results
            result = cur.fetchone()
            print("Database version:", result[0])