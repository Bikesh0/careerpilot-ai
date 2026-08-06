import sqlite3


class ApplicationTracker:

    def __init__(self):

        self.conn = sqlite3.connect(
            "data/careerpilot.db",
            check_same_thread=False
        )

        self.cursor = self.conn.cursor()

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS applications(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT,

            company TEXT,

            location TEXT,

            source TEXT,

            status TEXT DEFAULT 'Saved'

        )

        """)

        self.conn.commit()


    def add_application(
        self,
        title,
        company,
        location,
        source
    ):

        self.cursor.execute("""

        SELECT id

        FROM applications

        WHERE

        title=?

        AND

        company=?

        """,

        (

            title,

            company

        )

        )

        if self.cursor.fetchone():

            return False


        self.cursor.execute("""

        INSERT INTO applications(

            title,

            company,

            location,

            source

        )

        VALUES(

            ?,?,?,?

        )

        """,

        (

            title,

            company,

            location,

            source

        )

        )

        self.conn.commit()

        return True


    def all(self):

        self.cursor.execute("""

        SELECT *

        FROM applications

        ORDER BY id DESC

        """)

        return self.cursor.fetchall()


    def total(self):

        self.cursor.execute("""

        SELECT COUNT(*)

        FROM applications

        """)

        return self.cursor.fetchone()[0]