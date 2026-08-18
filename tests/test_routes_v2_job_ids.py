import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url):
    job = CanonicalJob(
        title="Security Engineer",
        company="Example",
        location="Helsinki",
        url=url,
        source="Example",
    )
    match = MatchResult(job_id=url, score=80.0)
    return RankedJob(job=job, match=match)


def test_search_jobs_assigns_local_ids_to_v2_jobs(monkeypatch):
    """
    Regression test.

    CanonicalJob has no "id" field, but the dashboard template links
    to /generate/<id>, /coverletter/<id>, and /save/<id>, which are
    resolved through manager.get_job(id). Before this fix, V2 jobs
    never received an id and manager.latest_jobs was never populated
    when V2 search succeeded, so every action link rendered as
    "/generate/" (empty id) and every action route returned
    "Job not found."
    """

    ranked = [
        make_ranked_job("https://example.test/jobs/1"),
        make_ranked_job("https://example.test/jobs/2"),
    ]

    class FakeService:
        def search(self, limit=50):
            return ranked

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: FakeService(),
    )

    jobs = routes._search_jobs(profile={})

    assert [job.id for job in jobs] == [0, 1]
    assert routes.manager.latest_jobs == jobs
    assert routes.manager.get_job(0) is jobs[0]
    assert routes.manager.get_job(1) is jobs[1]
