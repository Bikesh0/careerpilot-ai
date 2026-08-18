import sqlite3
from pathlib import Path


class ApplicationTracker:

    def __init__(self, database_path=None):
        """Create an application tracker.

        ``database_path`` is optional so production continues to use the
        existing ``data/careerpilot.db`` location. It also lets callers use
        an isolated SQLite file when running tests or maintenance scripts.
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
            check_same_thread=False
        )

        self.create_table()
        self.migrate_table()

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

                notes TEXT,

                job_url TEXT

            )
        """)

        self.db.commit()

    def migrate_table(self):

        """
        Add columns that may be missing from older
        CareerPilot database versions.

        Existing data is preserved.
        """

        cursor = self.db.cursor()

        cursor.execute(
            "PRAGMA table_info(applications)"
        )

        existing_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        required_columns = {
            "company": "TEXT",
            "title": "TEXT",
            "location": "TEXT",
            "source": "TEXT",
            "status": "TEXT",
            "applied_date": "TEXT",
            "resume_file": "TEXT",
            "cover_letter_file": "TEXT",
            "notes": "TEXT",
            "job_url": "TEXT",
        }

        for column, column_type in required_columns.items():

            if column not in existing_columns:

                cursor.execute(
                    f"""
                    ALTER TABLE applications
                    ADD COLUMN {column} {column_type}
                    """
                )

        self.db.commit()

    def find_existing(self, job_url="", company="", title=""):
        """
        Look up an already-saved application for the same job.

        job_url is the primary identity signal (unique per posting).
        company+title is a fallback for records with no job_url, kept
        for backward compatibility with rows saved before job_url was
        tracked.

        Returns the existing row id, or None if no match is found.
        """

        cursor = self.db.cursor()

        job_url = (job_url or "").strip()

        if job_url:

            cursor.execute("""
                SELECT id
                FROM applications
                WHERE job_url = ?
                LIMIT 1
            """, (
                job_url,
            ))

            existing = cursor.fetchone()

            if existing:
                return existing[0]

        if not company and not title:
            return None

        cursor.execute("""
            SELECT id
            FROM applications
            WHERE company = ?
            AND title = ?
            LIMIT 1
        """, (
            company,
            title,
        ))

        existing = cursor.fetchone()

        return existing[0] if existing else None

    def save(self, app):
        """
        Save an Application record.

        Idempotent: saving the same job twice (same job_url, or same
        company+title when no job_url is available) returns the
        existing row's id instead of inserting a duplicate.
        """

        existing_id = self.find_existing(
            job_url=getattr(app, "job_url", ""),
            company=app.company,
            title=app.title,
        )

        if existing_id is not None:
            return existing_id

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
                notes,
                job_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app.company,
            app.title,
            app.location,
            app.source,
            app.status,
            app.applied_date,
            app.resume_file,
            app.cover_letter_file,
            app.notes,
            getattr(app, "job_url", ""),
        ))

        self.db.commit()

        return cursor.lastrowid

    def save_job(self, job):

        """
        Save a CareerPilot job recommendation.

        'Recommended' means CareerPilot identified the
        job as worth considering. It does NOT mean the
        user has submitted an application.
        """

        if not isinstance(job, dict):

            raise TypeError(
                "save_job() expects a job dictionary"
            )

        company = job.get(
            "company",
            ""
        )

        title = job.get(
            "job_title",
            job.get(
                "title",
                ""
            )
        )

        location = job.get(
            "location",
            ""
        )

        source = job.get(
            "source",
            ""
        )

        notes = job.get(
            "notes",
            ""
        )

        job_url = job.get(
            "job_url",
            job.get(
                "url",
                ""
            )
        )

        existing_id = self.find_existing(
            job_url=job_url,
            company=company,
            title=title,
        )

        if existing_id is not None:
            return existing_id

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
                notes,
                job_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company,
            title,
            location,
            source,
            "Recommended",
            "",
            "",
            "",
            notes,
            job_url,
        ))

        self.db.commit()

        return cursor.lastrowid

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

        cursor.execute("""
            UPDATE applications
            SET status=?
            WHERE id=?
        """, (
            status,
            app_id
        ))

        self.db.commit()

    def delete(self, app_id):

        cursor = self.db.cursor()

        cursor.execute(
            "DELETE FROM applications WHERE id=?",
            (app_id,)
        )

        self.db.commit()

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
