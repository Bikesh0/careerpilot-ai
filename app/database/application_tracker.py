import sqlite3
from pathlib import Path

from app.database.models import Application


class ApplicationTracker:

    def __init__(self):

        Path("data").mkdir(exist_ok=True)

        self.db = sqlite3.connect(
            "data/careerpilot.db",
            check_same_thread=False
        )

        self.create_table()

    def create_table(self):

        cursor = self.db.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company TEXT,
            title TEXT,
            location TEXT,
            source TEXT,

            status TEXT,

            applied_date TEXT,

            resume_file TEXT,

            cover_letter_file TEXT,

            notes TEXT

        )
        """)

        self.db.commit()

    def save(self, app):

        cursor = self.db.cursor()

        cursor.execute("""

        INSERT INTO applications(

            company,
            title,
            location,
            source,
            status,
            applied_date,
            resume_file,
            cover_letter_file,
            notes

        )

        VALUES(?,?,?,?,?,?,?,?,?)

        """,

        (

            app.company,
            app.title,
            app.location,
            app.source,
            app.status,
            app.applied_date,
            app.resume_file,
            app.cover_letter_file,
            app.notes

        ))

        self.db.commit()

    def get_all(self):

        cursor = self.db.cursor()

        cursor.execute("""

        SELECT *

        FROM applications

        ORDER BY id DESC

        """)

        return cursor.fetchall()

    def update_status(self, app_id, status):

        cursor = self.db.cursor()

        cursor.execute(

            """

            UPDATE applications

            SET status=?

            WHERE id=?

            """,

            (

                status,

                app_id

            )

        )

        self.db.commit()

    def delete(self, app_id):

        cursor = self.db.cursor()

        cursor.execute(

            "DELETE FROM applications WHERE id=?",

            (app_id,)

        )

        self.db.commit()

    # ==========================
    # Dashboard Statistics
    # ==========================

    def count_all(self):

        cursor = self.db.cursor()

        cursor.execute(

            "SELECT COUNT(*) FROM applications"

        )

        return cursor.fetchone()[0]

    def count_status(self, status):

        cursor = self.db.cursor()

        cursor.execute(

            "SELECT COUNT(*) FROM applications WHERE status=?",

            (status,)

        )

        return cursor.fetchone()[0]