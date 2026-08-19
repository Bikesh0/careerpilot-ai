import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url, title="Security Engineer", description=""):
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


def test_interview_prep_is_gated_before_reaching_interview_stage(
    monkeypatch, tmp_path
):
    """
    Regression test for the core gating requirement: interview prep
    must not be generated (and must not call the LLM at all) for a job
    that hasn't been marked "Interview" or later.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")

    response = client.get("/interview/0")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "isn't available yet" in body


def test_interview_prep_unlocks_after_status_reaches_interview(
    monkeypatch, tmp_path
):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")
    client.get("/status/1/Interview")

    monkeypatch.setattr(
        routes.interview_prep_builder,
        "build",
        lambda profile, job, missing_skills=None: {
            "technical_questions": ["Explain how SIEM correlation rules work."],
            "scenario_questions": ["How would you triage a false-positive alert storm?"],
            "cv_questions": ["Walk me through your Cisco Networking Academy training."],
            "project_questions": ["Tell me about your CCNA coursework."],
            "explain_this_questions": ["Explain what a SOC playbook is."],
        },
    )

    response = client.get("/interview/0")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "SIEM correlation rules" in body
    assert "Cisco Networking Academy" in body


def test_interview_prep_unlocks_for_second_round_and_final_round_too(
    monkeypatch, tmp_path
):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")
    client.get("/status/1/Second%20Round")

    monkeypatch.setattr(
        routes.interview_prep_builder,
        "build",
        lambda profile, job, missing_skills=None: {
            "technical_questions": [],
            "scenario_questions": [],
            "cv_questions": [],
            "project_questions": [],
            "explain_this_questions": [],
        },
    )

    response = client.get("/interview/0")

    assert response.status_code == 200
    assert "isn't available yet" not in response.get_data(as_text=True)


def test_interview_prep_fails_gracefully_when_ollama_is_unavailable(
    monkeypatch, tmp_path
):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    client.get("/")
    client.get("/save/0")
    client.get("/status/1/Interview")

    def _raise(*args, **kwargs):
        raise RuntimeError("Ollama did not respond")

    monkeypatch.setattr(routes.interview_prep_builder, "build", _raise)

    response = client.get("/interview/0")

    assert response.status_code == 503


def test_dashboard_shows_interview_prep_button_only_when_ready(
    monkeypatch, tmp_path
):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    before = client.get("/")
    assert b"Interview Prep" not in before.data

    client.get("/save/0")
    client.get("/status/1/Interview")

    after = client.get("/")
    assert b"Interview Prep" in after.data


def test_bare_interview_route_explains_the_gate(monkeypatch, tmp_path):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, tmp_path, jobs)

    response = client.get("/interview")

    assert response.status_code == 200
    assert b"unlocks once" in response.data
