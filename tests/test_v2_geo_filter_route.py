import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url, location):
    job = CanonicalJob(
        title="Security Engineer",
        company="Example Corp",
        location=location,
        url=url,
        source="Jobly",
    )
    match = MatchResult(job_id=url, score=80.0)
    return RankedJob(job=job, match=match)


class FakeV2Service:
    def __init__(self, jobs):
        self._jobs = jobs

    def search(self, limit=50):
        return self._jobs


def test_dashboard_excludes_confidently_non_european_v2_jobs_by_default(
    monkeypatch,
):
    jobs = [
        make_ranked_job("https://example.test/jobs/1", "Helsinki, Finland"),
        make_ranked_job("https://example.test/jobs/2", "Bangalore, India"),
    ]

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: FakeV2Service(jobs),
    )

    from webapp import app

    client = app.test_client()
    response = client.get("/")
    body = response.get_data(as_text=True)

    assert "Helsinki, Finland" in body
    assert "Bangalore, India" not in body
