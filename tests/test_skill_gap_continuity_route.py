import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


class FakeV2Service:
    def __init__(self, jobs):
        self._jobs = jobs

    def search(self, limit=50):
        return self._jobs


class FakeProjectService:
    """
    Stands in for app.services.project_service.ProjectService so this
    test doesn't depend on (or mutate) the real project-tracking
    database - only the shape ProjectService.get_all() returns.
    """

    def __init__(self, projects):
        self._projects = projects

    def get_all(self):
        return self._projects

    def verified_skill_keys(self):
        return {
            project["skill_key"]
            for project in self._projects
            if project["status"] == "Verified"
        }


def test_analyze_route_offers_continuation_for_an_in_progress_project(
    monkeypatch,
):
    jobs = [
        RankedJob(
            job=CanonicalJob(
                title="Cloud Engineer",
                company="Example Corp",
                location="Helsinki, Finland",
                url="https://example.test/jobs/1",
                source="Jobly",
                description="Requirements: SOC experience required.",
            ),
            match=MatchResult(job_id="https://example.test/jobs/1", score=80.0),
        )
    ]

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes, "create_v2_service", lambda profile=None: FakeV2Service(jobs)
    )
    monkeypatch.setattr(
        routes,
        "ProjectService",
        lambda: FakeProjectService([
            {
                "id": 4,
                "skill_key": "soc operations",
                "skill_display": "SOC Operations",
                "title": "SOC triage documentation",
                "status": "Planned",
            }
        ]),
    )

    from webapp import app

    client = app.test_client()
    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Continue your project (Planned)" in body
    assert 'href="/projects/4"' in body
