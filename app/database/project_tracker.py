import sqlite3
from pathlib import Path


# Never set by anything other than an explicit user action - see
# docs/PRODUCT_VISION.md's "Project tracking and the AI project coach".
# "Verified" is deliberately a separate step from "Completed": the user
# marks it Verified once they've actually produced the real evidence
# (pushed to GitHub, written the README, etc.) - that's the gate for
# app/ai/cv_strength.py to count it as skill evidence, and for a CV
# bullet to be generatable at all.
PROJECT_STATUSES = ("Planned", "In Progress", "Completed", "Verified")


class ProjectTracker:

    def __init__(self, database_path=None):
        """
        Create a project tracker.

        ``database_path`` is optional so production continues to use
        the existing ``data/careerpilot.db`` location (the same
        database file as ApplicationTracker - one local database for
        this single-user tool, not a separate file). Also lets callers
        use an isolated SQLite file for tests.
        """

        database_path = (
            Path(database_path)
            if database_path is not None
            else Path("data") / "careerpilot.db"
        )

        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.db = sqlite3.connect(
            str(database_path),
            check_same_thread=False,
        )

        self.create_table()

    def create_table(self):

        cursor = self.db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                skill_key TEXT,
                skill_display TEXT,

                title TEXT,
                description TEXT,

                status TEXT,

                created_date TEXT,
                updated_date TEXT,

                source_job_url TEXT,

                notes TEXT,

                cv_bullet TEXT

            )
        """)

        self.db.commit()

    def create(self, project):
        cursor = self.db.cursor()

        cursor.execute("""
            INSERT INTO projects(
                skill_key,
                skill_display,
                title,
                description,
                status,
                created_date,
                updated_date,
                source_job_url,
                notes,
                cv_bullet
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project.skill_key,
            project.skill_display,
            project.title,
            project.description,
            project.status,
            project.created_date,
            project.created_date,
            project.source_job_url,
            project.notes,
            project.cv_bullet,
        ))

        self.db.commit()

        return cursor.lastrowid

    def get_all(self):
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT *
            FROM projects
            ORDER BY id DESC
        """)

        return cursor.fetchall()

    def get(self, project_id):
        cursor = self.db.cursor()

        cursor.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
        )

        return cursor.fetchone()

    def get_verified_by_skill_key(self, skill_key):
        """
        All Verified projects for a given skill - what
        app.ai.cv_strength uses to recognize real, completed practical
        evidence beyond what's in the profile's experience text.
        """

        cursor = self.db.cursor()

        cursor.execute(
            """
            SELECT * FROM projects
            WHERE skill_key = ? AND status = 'Verified'
            """,
            (skill_key,),
        )

        return cursor.fetchall()

    def update_status(self, project_id, status, updated_date):
        cursor = self.db.cursor()

        cursor.execute(
            """
            UPDATE projects
            SET status = ?, updated_date = ?
            WHERE id = ?
            """,
            (status, updated_date, project_id),
        )

        self.db.commit()

    def append_notes(self, project_id, note_entry, updated_date):
        """
        Append one timestamped entry to a project's notes - used to
        keep a running record of AI-coach exchanges. Never overwrites
        prior notes.
        """

        cursor = self.db.cursor()

        cursor.execute(
            "SELECT notes FROM projects WHERE id = ?",
            (project_id,),
        )

        row = cursor.fetchone()
        existing = (row[0] if row and row[0] else "").strip()

        combined = (
            f"{existing}\n\n{note_entry}".strip()
            if existing
            else note_entry
        )

        cursor.execute(
            """
            UPDATE projects
            SET notes = ?, updated_date = ?
            WHERE id = ?
            """,
            (combined, updated_date, project_id),
        )

        self.db.commit()

    def set_cv_bullet(self, project_id, cv_bullet, updated_date):
        cursor = self.db.cursor()

        cursor.execute(
            """
            UPDATE projects
            SET cv_bullet = ?, updated_date = ?
            WHERE id = ?
            """,
            (cv_bullet, updated_date, project_id),
        )

        self.db.commit()

    def count_status(self, status):
        cursor = self.db.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM projects WHERE status = ?",
            (status,),
        )

        return cursor.fetchone()[0]
