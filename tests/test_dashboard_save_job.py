import sqlite3

import app.web.routes as routes
from app.database.application_tracker import ApplicationTracker
from app.database.models import Application
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url, title="Security Engineer"):
    job = CanonicalJob(
        title=title,
        company="Example Corp",
        location="Helsinki",
        url=url,
        source="Duunitori",
    )
    match = MatchResult(job_id=url, score=80.0)
    return RankedJob(job=job, match=match)


class FakeV2Service:
    def __init__(self, jobs):
        self._jobs = jobs

    def search(self, limit=50):
        return self._jobs


def _client(monkeypatch, tmp_path, jobs):
    """
    Build a Flask test client wired to a fake V2 search and an isolated
    on-disk SQLite database.

    ApplicationTracker resolves its database path relative to the
    current working directory (Path("data") / "careerpilot.db"), so
    isolating it for a test means chdir-ing into a temp directory before
    any request runs - ApplicationService/ApplicationTracker are
    constructed fresh per request in app.web.routes, not cached at
    import time, so this correctly isolates each test's data.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: FakeV2Service(jobs),
    )

    from webapp import app

    return app.test_client(), tmp_path / "data" / "careerpilot.db"


def test_save_job_from_dashboard_persists_and_appears_on_applications_page(
    monkeypatch,
    tmp_path,
):
    """
    Regression test - traces the complete flow end to end: dashboard ->
    Save Job link -> /save/<id> route -> ApplicationService ->
    ApplicationTracker -> SQLite -> /applications page.

    Also covers a second bug found alongside the duplicate-row issue:
    job_url was accepted by Application and ApplicationService.save_job()
    but silently dropped by ApplicationTracker - it was never in the
    applications table's column list or its INSERT statement at all.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client, db_path = _client(monkeypatch, tmp_path, jobs)

    dashboard_response = client.get("/")
    assert dashboard_response.status_code == 200

    save_response = client.get("/save/0")
    assert save_response.status_code == 302

    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        """
        SELECT company, title, location, source, status, job_url
        FROM applications
        """
    ).fetchall()
    connection.close()

    assert rows == [
        (
            "Example Corp",
            "Security Engineer",
            "Helsinki",
            "Duunitori",
            "Saved",
            "https://example.test/jobs/1",
        ),
    ]

    applications_response = client.get("/applications")
    assert applications_response.status_code == 200

    body = applications_response.get_data(as_text=True)
    assert "Example Corp" in body
    assert "Security Engineer" in body


def test_saving_the_same_job_twice_does_not_create_a_duplicate_record(
    monkeypatch,
    tmp_path,
):
    """
    Regression test.

    ApplicationTracker.save() - the method the dashboard's /save/<id>
    route actually calls via ApplicationService.save_job() - had no
    duplicate detection at all. A *different*, unused sibling method
    (save_job(), only ever called from the V1 CLI in main.py) had
    dedup logic, but the dashboard never went through it, so clicking
    "Save Job" twice on the same posting inserted two full duplicate
    rows.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client, db_path = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")
    client.get("/save/0")

    connection = sqlite3.connect(db_path)
    count = connection.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]
    connection.close()

    assert count == 1


def test_save_job_works_correctly_for_v2_canonical_jobs(
    monkeypatch,
    tmp_path,
):
    """
    Regression test: saving must work for V2's CanonicalJob objects, not
    only V1 Job objects - the dashboard's job list is made of
    CanonicalJob instances whenever V2 search is enabled, which is the
    primary supported path.
    """

    ranked = make_ranked_job(
        "https://example.test/jobs/42",
        title="Cloud Security Engineer",
    )
    assert isinstance(ranked.job, CanonicalJob)

    client, db_path = _client(monkeypatch, tmp_path, [ranked])

    client.get("/")
    save_response = client.get("/save/0")
    assert save_response.status_code == 302

    connection = sqlite3.connect(db_path)
    row = connection.execute(
        "SELECT title, job_url FROM applications"
    ).fetchone()
    connection.close()

    assert row == (
        "Cloud Security Engineer",
        "https://example.test/jobs/42",
    )


def test_application_tracker_save_is_idempotent_by_job_url(tmp_path):
    """
    Unit-level regression test for the same fix, isolated from Flask:
    ApplicationTracker.save() must not insert a second row for a
    record with the same job_url.
    """

    tracker = ApplicationTracker(
        database_path=tmp_path / "careerpilot.db"
    )

    record = Application(
        company="Example Corp",
        title="Security Engineer",
        location="Helsinki",
        source="Duunitori",
        status="Saved",
        applied_date="2026-08-18",
        job_url="https://example.test/jobs/1",
    )

    first_id = tracker.save(record)
    second_id = tracker.save(record)

    assert first_id == second_id
    assert tracker.count_all() == 1
