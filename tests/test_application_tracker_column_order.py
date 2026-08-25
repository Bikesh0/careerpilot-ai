import sqlite3

from app.database.application_tracker import ApplicationTracker
from app.database.models import Application


def _create_old_order_table(database_path):
    """
    Recreate the exact physical column order data/careerpilot.db's
    applications table has today (id, title, company, ... - the
    original schema, before create_table() was changed to declare
    company before title). migrate_table() only ever ADD COLUMNs, it
    never reorders existing ones, so any database file created before
    that change keeps this order forever.
    """

    connection = sqlite3.connect(str(database_path))
    connection.execute(
        """
        CREATE TABLE applications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            source TEXT,
            status TEXT DEFAULT 'Saved',
            applied_date TEXT,
            resume_file TEXT,
            cover_letter_file TEXT,
            notes TEXT,
            job_url TEXT
        )
        """
    )
    connection.commit()
    connection.close()


def test_get_all_returns_correct_columns_against_a_pre_existing_table_with_old_column_order(
    tmp_path,
):
    database_path = tmp_path / "careerpilot.db"
    _create_old_order_table(database_path)

    tracker = ApplicationTracker(database_path=database_path)
    tracker.save(
        Application(
            company="Example Corp",
            title="SOC Analyst",
            location="Helsinki",
            source="Example",
            status="Saved",
            applied_date="2026-08-15",
            job_url="https://example.test/jobs/1",
        )
    )

    rows = tracker.get_all()
    assert len(rows) == 1

    row = rows[0]
    # Positional indices match get_all()'s named SELECT, not whatever
    # order this specific file's columns happen to be in physically -
    # this is exactly what templates/applications.html relies on
    # (app[1] = Company, app[2] = Position).
    assert row[1] == "Example Corp"
    assert row[2] == "SOC Analyst"
    assert row[5] == "Saved"
    assert row[6] == "2026-08-15"
