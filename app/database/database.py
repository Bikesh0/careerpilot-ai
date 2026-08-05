import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_PATH = os.path.join(DATA_DIR, "careerpilot.db")


def get_connection():

    return sqlite3.connect(
        DATABASE_PATH
    )



def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()



    # Jobs table

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT,

            company TEXT,

            location TEXT,

            description TEXT,

            source TEXT,

            url TEXT,

            match_score INTEGER,

            decision TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )



    # Application tracker table

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT,

            company TEXT,

            url TEXT,

            status TEXT DEFAULT 'Saved',

            created TEXT,

            notes TEXT

        )
        """
    )



    conn.commit()

    conn.close()



    print(
        "Database initialized"
    )



def job_exists(
    title,
    company
):

    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT id

        FROM jobs

        WHERE title = ?

        AND company = ?

        """,
        (
            title,
            company
        )
    )



    result = cursor.fetchone()



    conn.close()



    return result is not None