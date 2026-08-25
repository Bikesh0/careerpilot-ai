import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


class FakeV2Service:
    def __init__(self, jobs):
        self._jobs = jobs

    def search(self, limit=50):
        return self._jobs


def _client(monkeypatch, jobs):
    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes, "create_v2_service", lambda profile=None: FakeV2Service(jobs)
    )

    from webapp import app

    return app.test_client()


def test_analyze_route_shows_three_separate_hiring_perspectives(monkeypatch):
    job = CanonicalJob(
        title="Cloud Security Engineer",
        company="Acme",
        location="Helsinki, Finland",
        url="https://example.test/jobs/1",
        source="Jobly",
        description="Requirements: AWS, IAM, cloud security required.",
    )
    jobs = [RankedJob(job=job, match=MatchResult(job_id="1", score=70.0))]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "ATS / Keyword Screening" in body
    assert "HR / Recruiter" in body
    assert "Technical Manager" in body


def test_analyze_route_shows_the_job_career_family(monkeypatch):
    job = CanonicalJob(
        title="Cloud Security Engineer",
        company="Acme",
        location="Helsinki, Finland",
        url="https://example.test/jobs/1",
        source="Jobly",
        description="Requirements: AWS, IAM, cloud security required.",
    )
    jobs = [RankedJob(job=job, match=MatchResult(job_id="1", score=70.0))]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert '<span class="sg-badge sg-family-primary">Cloud Security</span>' in body
