import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob
from app.services.project_service import ProjectService


def make_ranked_job(url, title="Platform Engineer", description=""):
    job = CanonicalJob(
        title=title,
        company="Example Corp",
        location="Helsinki",
        url=url,
        source="Jobly",
        description=description,
    )
    match = MatchResult(job_id=url, score=50.0)
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


def test_skill_gap_page_links_to_start_a_project(monkeypatch, tmp_path):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Terraform experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert "/projects/start/0/terraform" in body


def test_cv_strength_page_links_to_the_job_independent_start_route(
    monkeypatch, tmp_path
):
    """
    Layer 1 (CV strength) has no job context at all, so its "Start this
    project" links must use the job-independent route, not the
    Layer 2 one that requires a job_id.
    """

    monkeypatch.chdir(tmp_path)

    from webapp import app

    client = app.test_client()
    response = client.get("/cv-strength")
    body = response.get_data(as_text=True)

    assert "/projects/start-general/" in body
    assert "/projects/start/" not in body


def test_general_start_project_route_works_without_a_job(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    from webapp import app

    client = app.test_client()
    response = client.get("/projects/start-general/python")

    assert response.status_code == 302

    detail = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Python" in detail


def test_general_start_project_route_404s_for_unknown_skill(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    from webapp import app

    client = app.test_client()
    response = client.get("/projects/start-general/not-a-real-skill")

    assert response.status_code == 404


def test_starting_a_project_creates_it_with_planned_status(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Terraform experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")

    response = client.get("/projects/start/0/terraform")
    assert response.status_code == 302
    assert response.headers["Location"] == "/projects/1"

    detail = client.get("/projects/1")
    body = detail.get_data(as_text=True)

    assert "Terraform" in body
    assert "Planned" in body


def test_starting_a_project_for_an_unknown_skill_key_404s(
    monkeypatch, tmp_path
):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")

    response = client.get("/projects/start/0/not-a-real-skill")
    assert response.status_code == 404


def test_project_status_changes_only_via_explicit_route_call(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Docker experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/docker")

    before = client.get("/projects/1").get_data(as_text=True)
    assert "/projects/1/status/Planned" in before
    assert "/projects/1/status/In%20Progress" in before
    assert ProjectService().get(1)["status"] == "Planned"

    response = client.get("/projects/1/status/In%20Progress")
    assert response.status_code == 302

    assert ProjectService().get(1)["status"] == "In Progress"


def test_cv_bullet_is_gated_to_verified_status(monkeypatch, tmp_path):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Git experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/git")

    response = client.get("/projects/1/cv-bullet")
    assert response.status_code == 400


def test_cv_bullet_is_drafted_once_verified_and_stays_grounded(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Git experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/git")
    client.get("/projects/1/status/Verified")

    monkeypatch.setattr(
        routes.project_coach,
        "draft_cv_bullet",
        lambda project: (
            f"Built a public GitHub portfolio repository as part of "
            f"'{project['title']}'."
        ),
    )

    response = client.get("/projects/1/cv-bullet")
    assert response.status_code == 302

    detail = client.get("/projects/1").get_data(as_text=True)
    assert "public GitHub portfolio repository" in detail


def test_get_plan_appends_a_step_by_step_plan_to_notes(monkeypatch, tmp_path):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Terraform experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/terraform")

    monkeypatch.setattr(
        routes.project_coach,
        "plan",
        lambda project: "Day 1: Install Terraform. Checkpoint: terraform -version works.",
    )

    response = client.get("/projects/1/plan")
    assert response.status_code == 302

    detail = client.get("/projects/1").get_data(as_text=True)
    assert "Day 1: Install Terraform" in detail


def test_get_plan_degrades_gracefully_when_ollama_is_unavailable(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Terraform experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/terraform")

    def _raise(*args, **kwargs):
        raise RuntimeError("Ollama did not respond")

    monkeypatch.setattr(routes.project_coach, "plan", _raise)

    response = client.get("/projects/1/plan")
    assert response.status_code == 200
    assert "unavailable" in response.get_data(as_text=True).lower()


def test_review_appends_submission_and_feedback_to_notes(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Docker experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/docker")

    monkeypatch.setattr(
        routes.project_coach,
        "review",
        lambda project, submission: "Your Dockerfile looks reasonable, but pin the base image version.",
    )

    response = client.post(
        "/projects/1/review",
        data={"submission": "FROM python:latest\nRUN pip install flask"},
    )
    assert response.status_code == 302

    detail = client.get("/projects/1").get_data(as_text=True)
    assert "FROM python:latest" in detail
    assert "pin the base image version" in detail


def test_review_degrades_gracefully_when_ollama_is_unavailable(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Docker experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/docker")

    def _raise(*args, **kwargs):
        raise RuntimeError("Ollama did not respond")

    monkeypatch.setattr(routes.project_coach, "review", _raise)

    response = client.post(
        "/projects/1/review",
        data={"submission": "some code"},
    )
    assert response.status_code == 200
    assert "unavailable" in response.get_data(as_text=True).lower()


def test_ask_coach_appends_to_notes(monkeypatch, tmp_path):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Kubernetes experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/kubernetes")

    monkeypatch.setattr(
        routes.project_coach,
        "ask",
        lambda project, question: "Use kubectl apply -f to deploy a manifest.",
    )

    response = client.post(
        "/projects/1/ask",
        data={"question": "How do I deploy a manifest?"},
    )
    assert response.status_code == 302

    detail = client.get("/projects/1").get_data(as_text=True)
    assert "kubectl apply" in detail


def test_ask_coach_degrades_gracefully_when_ollama_is_unavailable(
    monkeypatch, tmp_path
):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Kubernetes experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/kubernetes")

    def _raise(*args, **kwargs):
        raise RuntimeError("Ollama did not respond")

    monkeypatch.setattr(routes.project_coach, "ask", _raise)

    response = client.post(
        "/projects/1/ask",
        data={"question": "How do I deploy a manifest?"},
    )

    assert response.status_code == 200
    assert "unavailable" in response.get_data(as_text=True).lower()


def test_projects_list_page_shows_started_projects(monkeypatch, tmp_path):
    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description="Requirements: Splunk experience required.",
        )
    ]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/analyze/0")
    client.get("/projects/start/0/splunk")

    response = client.get("/projects")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Splunk log ingestion lab" in body


def test_unknown_project_id_404s(monkeypatch, tmp_path):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    response = client.get("/projects/999")
    assert response.status_code == 404


def test_sidebar_links_to_projects(monkeypatch, tmp_path):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    response = client.get("/projects")
    assert b'href="/projects"' in response.data
