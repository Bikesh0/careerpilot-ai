from app.database import database
from app.database.application_tracker import ApplicationTracker
from app.database.models import Application
from app.search.job_memory import JobMemory


def test_temporary_sqlite_supports_job_memory_and_applications(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "careerpilot.db"
    monkeypatch.setattr(database, "DATABASE_PATH", str(database_path))
    database.initialize_database()

    connection = database.get_connection()
    connection.execute(
        """
        INSERT INTO jobs (title, company, location, description, source, url)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Security Engineer",
            "Example Corp",
            "Helsinki",
            "Linux and SIEM",
            "Example",
            "https://example.test/jobs/1",
        ),
    )
    connection.commit()
    connection.close()

    memory = JobMemory()
    assert memory.filter_new_jobs(
        [
            {"title": "Security Engineer", "company": "Example Corp"},
            {"title": "SOC Analyst", "company": "Example Corp"},
        ]
    ) == [{"title": "SOC Analyst", "company": "Example Corp"}]

    tracker = ApplicationTracker(database_path=database_path)
    tracker.save(
        Application(
            company="Example Corp",
            title="SOC Analyst",
            location="Helsinki",
            source="Example",
            status="Saved",
            applied_date="2026-08-15",
            job_url="https://example.test/jobs/2",
        )
    )

    assert tracker.count_all() == 1
    assert tracker.count_status("Saved") == 1
