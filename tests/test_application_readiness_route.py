import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url, score, description="", title="Cloud Security Engineer"):
    job = CanonicalJob(
        title=title,
        company="Example Corp",
        location="Helsinki, Finland",
        url=url,
        source="Jobly",
        description=description,
    )
    match = MatchResult(job_id=url, score=score)
    return RankedJob(job=job, match=match)


class FakeV2Service:
    def __init__(self, jobs):
        self._jobs = jobs

    def search(self, limit=50):
        return self._jobs


def _client(monkeypatch, jobs):
    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: FakeV2Service(jobs),
    )

    from webapp import app

    return app.test_client()


def test_dashboard_cards_show_an_application_readiness_badge(monkeypatch):
    jobs = [make_ranked_job("https://example.test/jobs/1", score=85.0)]
    client = _client(monkeypatch, jobs)

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "cp-readiness" in body
    assert "Apply now" in body


def test_analyze_page_shows_a_readiness_verdict_when_requirements_were_extracted(
    monkeypatch,
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            score=85.0,
            description="Requirements: AWS and Python required.",
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<p class="sg-readiness">' in body


def test_analyze_page_omits_readiness_verdict_when_nothing_could_be_extracted(
    monkeypatch,
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            score=20.0,
            description="",
            title="Front Desk Coordinator",
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<p class="sg-readiness">' not in body
