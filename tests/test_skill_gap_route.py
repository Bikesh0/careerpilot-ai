import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url, title="Cloud Security Engineer", description=""):
    job = CanonicalJob(
        title=title,
        company="Example Corp",
        location="Helsinki",
        url=url,
        source="Jobly",
        description=description,
    )
    match = MatchResult(job_id=url, score=80.0)
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


def test_dashboard_links_each_job_to_its_skill_gap_analysis(monkeypatch):
    """
    Regression test for the UX requirement: the skill-gap analysis must
    be reachable directly from the dashboard, not just via a URL the
    user has to guess.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, jobs)

    response = client.get("/")

    assert response.status_code == 200
    assert b'href="/analyze/0"' in response.data


def test_analyze_route_renders_required_and_recommended_actions(
    monkeypatch,
):
    """
    End-to-end regression test tracing the full flow the requirement
    asks for: job requirement -> current skill -> gap -> recommended
    action, all visible on one rendered page.
    """

    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            title="Platform Engineer",
            description=(
                "Requirements: strong Terraform and Kubernetes skills "
                "are required. Linux experience is also required.\n"
                "Nice to have: Ansible experience is a plus.\n"
            ),
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")

    assert response.status_code == 200

    body = response.get_data(as_text=True)

    assert "Platform Engineer" in body
    assert "Required skills" in body
    assert "Terraform" in body
    assert "Kubernetes" in body
    assert "Recommended next steps" in body
    assert "CV / profile improvement suggestions" in body


def test_analyze_route_returns_404_for_unknown_job_id(monkeypatch):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/99")

    assert response.status_code == 404
