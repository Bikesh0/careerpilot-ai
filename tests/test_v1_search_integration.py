from app.ai.matcher import JobMatcher
from app.database import database
from app.search.filter import JobFilter
from app.search.job_memory import JobMemory
from app.search.manager import SearchManager
from app.search.sources.greenhouse_source import GreenhouseSource


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_v1_search_pipeline_uses_mocked_source_and_temporary_sqlite(
    monkeypatch,
    tmp_path,
    greenhouse_payload,
    candidate_profile,
):
    database_path = tmp_path / "careerpilot.db"
    monkeypatch.setattr(database, "DATABASE_PATH", str(database_path))
    database.initialize_database()

    monkeypatch.setattr(
        "app.search.sources.greenhouse_source.requests.get",
        lambda url, timeout: MockResponse(greenhouse_payload),
    )

    manager = SearchManager()
    manager.searchers = [GreenhouseSource()]
    discovered_jobs = manager.search_jobs()

    assert len(discovered_jobs) == 1
    assert JobMemory().filter_new_jobs(
        [
            {
                "title": discovered_jobs[0].title,
                "company": discovered_jobs[0].company,
            }
        ]
    )

    relevant_jobs = JobFilter().cybersecurity_only(discovered_jobs)
    ranked_jobs = JobMatcher().rank_jobs(
        relevant_jobs,
        candidate_profile,
    )

    assert len(ranked_jobs) == 1
    assert ranked_jobs[0]["job"]["source"] == "Greenhouse"
    assert ranked_jobs[0]["match_score"] >= 50

    connection = database.get_connection()
    connection.execute(
        "INSERT INTO jobs (title, company) VALUES (?, ?)",
        (discovered_jobs[0].title, discovered_jobs[0].company),
    )
    connection.commit()
    connection.close()

    assert JobMemory().filter_new_jobs(
        [
            {
                "title": discovered_jobs[0].title,
                "company": discovered_jobs[0].company,
            }
        ]
    ) == []
