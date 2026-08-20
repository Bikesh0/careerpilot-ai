import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url):
    job = CanonicalJob(
        title="Security Engineer",
        company="Example Corp",
        location="Helsinki",
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


def _client(monkeypatch, tmp_path, jobs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: FakeV2Service(jobs),
    )

    from webapp import app

    return app.test_client()


def test_status_route_accepts_multi_word_statuses_via_url_encoding(
    monkeypatch, tmp_path
):
    """
    Regression test: "Second Round" and "Final Round" are multi-word
    statuses. The applications template links to them URL-encoded
    (%20), and the plain /status/<id>/<status> route must decode that
    back to the exact status string stored in SQLite - not a truncated
    or mangled one.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")

    response = client.get("/status/1/Second%20Round")
    assert response.status_code == 302

    applications_response = client.get("/applications")
    body = applications_response.get_data(as_text=True)

    assert "Second Round" in body
    assert "second round" in body.lower()


def test_applications_page_shows_funnel_stats(monkeypatch, tmp_path):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")
    client.get("/status/1/Interview")

    response = client.get("/applications")
    body = response.get_data(as_text=True)

    assert "reached interview or later" in body


def test_withdrawn_is_a_valid_status_and_counted_separately(
    monkeypatch, tmp_path
):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")

    response = client.get("/status/1/Withdrawn")
    assert response.status_code == 302

    from app.services.application_service import ApplicationService

    stats = ApplicationService().statistics()
    assert stats["withdrawn"] == 1
    # Withdrawn is a terminal, non-interview-stage status, like Rejected.
    assert stats["interview_stage_or_later"] == 0


def test_dashboard_gauge_is_labeled_profile_match_not_bare_match(
    monkeypatch, tmp_path
):
    """
    The gauge label stays "Profile Match" rather than a bare "Match" -
    a small, permanent clarification of what the number is. The longer
    explanatory paragraph that used to sit above the job list was
    removed at the user's explicit request (it read as unwanted
    boilerplate/disclaimer text cluttering the dashboard) - see
    docs/PRODUCT_VISION.md.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert "Profile Match" in body
    assert "What \"Profile Match\" means" not in body
    assert "hiring probability" not in body.lower()


def test_every_job_card_has_a_working_apply_link(monkeypatch, tmp_path):
    """
    Regression test for the mission's explicit requirement: every job
    shown to the user must have an obvious Apply link pointing at the
    real external posting URL.
    """

    job_url = "https://example.test/jobs/1"
    jobs = [make_ranked_job(job_url)]
    client = _client(monkeypatch, tmp_path, jobs)

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert f'href="{job_url}"' in body
    assert "Apply" in body


def test_dashboard_shows_funnel_insight_banner(monkeypatch, tmp_path):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert "not enough applications" in body.lower()
