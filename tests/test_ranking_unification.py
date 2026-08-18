import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob
from webapp import app


def make_ranked_job(url, title, score, reasons=None, matched_skills=None):
    job = CanonicalJob(
        title=title,
        company="Example Corp",
        location="Helsinki",
        url=url,
        source="Duunitori",
        description="lead architect role requiring 8 years experience",
    )
    match = MatchResult(
        job_id=url,
        score=score,
        reasons=reasons or ["Target job title matched"],
        matched_skills=matched_skills or ["Linux"],
        missing_skills=["Splunk"],
        title_score=100.0,
        skill_score=50.0,
        location_score=100.0,
        seniority_score=5.0,
    )
    return RankedJob(job=job, match=match)


class FakeV2Service:
    def __init__(self, ranked):
        self._ranked = ranked

    def search(self, limit=50):
        return self._ranked


def _v2_client(monkeypatch, ranked):
    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: FakeV2Service(ranked),
    )
    return app.test_client()


def test_dashboard_uses_v2_score_and_reasons_when_v2_is_enabled(monkeypatch):
    """
    Regression test: proves the dashboard renders V2's own scoring, not
    a legacy-matcher re-score of the same job.

    The job description here ("lead architect role requiring 8 years
    experience") would earn the legacy matcher a large mismatch
    penalty and a very different score from the one V2 already
    computed (93). "Target job title matched" is a reason string only
    V2's matcher ever produces (app/search/v2/matching/matcher.py) -
    the legacy matcher's vocabulary is entirely different
    (mismatch_reasons like "lead-level role", "high experience
    requirement"). Seeing both the exact V2 score and this exact
    phrase in the rendered HTML is only possible if V2's MatchResult
    is what actually reached the template.
    """

    ranked = [
        make_ranked_job(
            "https://example.test/jobs/1",
            "Staff Security Engineer",
            score=93.0,
            reasons=["Target job title matched", "Matched 1 profile skills"],
        ),
    ]

    client = _v2_client(monkeypatch, ranked)

    response = client.get("/")
    assert response.status_code == 200

    body = response.get_data(as_text=True)
    assert "93%" in body
    assert "Target job title matched" in body
    assert "Matched 1 profile skills" in body
    assert "Staff Security Engineer" in body


def test_dashboard_preserves_v2_ranking_order(monkeypatch):
    """
    Regression test: the dashboard must not re-sort V2's already-ranked
    results. Three jobs are constructed with scores in descending
    order (91, 60, 12) - if the presentation layer re-sorted or
    re-scored them through the legacy matcher (which would judge the
    "Director of Security" job very differently), the order or scores
    would not match what's asserted here.
    """

    ranked = [
        make_ranked_job(
            "https://example.test/jobs/first",
            "Security Engineer",
            score=91.0,
        ),
        make_ranked_job(
            "https://example.test/jobs/second",
            "Cloud Engineer",
            score=60.0,
        ),
        make_ranked_job(
            "https://example.test/jobs/third",
            "Director of Security",
            score=12.0,
        ),
    ]

    client = _v2_client(monkeypatch, ranked)

    response = client.get("/")
    body = response.get_data(as_text=True)

    first_index = body.index("Security Engineer")
    second_index = body.index("Cloud Engineer")
    third_index = body.index("Director of Security")

    assert first_index < second_index < third_index
    assert "91%" in body
    assert "60%" in body
    assert "12%" in body


def test_dashboard_falls_back_to_legacy_matcher_when_v2_is_disabled(monkeypatch):
    """
    Regression test: legacy behavior must be unchanged when V2 is
    disabled. The dashboard must not show any V2-only reason text
    (match_reasons is a key the legacy dict-based ranked jobs never
    have), and manager.search_jobs() (the V1 path) must be what
    actually produced the job list.
    """

    monkeypatch.setattr(routes, "v2_enabled", lambda: False)

    calls = []

    def fake_search_jobs():
        calls.append(True)
        return []

    monkeypatch.setattr(routes.manager, "search_jobs", fake_search_jobs)
    monkeypatch.setattr(routes.manager, "latest_jobs", [], raising=False)

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert calls == [True]

    body = response.get_data(as_text=True)
    assert "Target job title matched" not in body


def test_v2_presented_jobs_falls_back_to_legacy_matcher_on_presentation_error(
    monkeypatch,
):
    """
    If adapting V2's results for display ever raises, the dashboard
    should still render via the legacy matcher rather than crash the
    whole request - matching the existing fail-soft convention used
    everywhere else in this route module.
    """

    ranked = [make_ranked_job("https://example.test/jobs/1", "Security Engineer", 80.0)]

    client = _v2_client(monkeypatch, ranked)

    def broken_presentation(jobs):
        raise RuntimeError("boom")

    monkeypatch.setattr(routes, "_present_v2_ranked_jobs", broken_presentation)

    response = client.get("/")

    assert response.status_code == 200


def test_save_job_still_works_through_the_v2_presentation_path(monkeypatch, tmp_path):
    """
    Regression test: /save/<id> must still resolve the correct job
    (via manager.latest_jobs, populated by _search_jobs regardless of
    which presentation path _rank_jobs takes) once the dashboard is
    driven by V2's own scoring instead of the legacy matcher.
    """

    monkeypatch.chdir(tmp_path)

    ranked = [
        make_ranked_job("https://example.test/jobs/1", "Security Engineer", 80.0),
    ]

    client = _v2_client(monkeypatch, ranked)

    dashboard_response = client.get("/")
    assert dashboard_response.status_code == 200

    save_response = client.get("/save/0")
    assert save_response.status_code == 302

    applications_response = client.get("/applications")
    assert "Security Engineer" in applications_response.get_data(as_text=True)


def test_generate_and_coverletter_routes_still_resolve_v2_jobs(monkeypatch):
    """
    Regression test: /generate/<id> and /coverletter/<id> must still
    find the job via manager.latest_jobs after the ranking-unification
    change. The AI builders are mocked (a real call would hit the
    local Ollama timeout, up to 30s by default - avoided here the same
    way the rest of the suite avoids any live Ollama dependency) - this
    test only proves job resolution still works, i.e. the routes don't
    return "Job not found."
    """

    ranked = [
        make_ranked_job("https://example.test/jobs/1", "Security Engineer", 80.0),
    ]

    client = _v2_client(monkeypatch, ranked)

    monkeypatch.setattr(
        routes.document_ai.resume_builder,
        "build",
        lambda profile, job: {"summary": "", "skills": [], "experience": []},
    )
    monkeypatch.setattr(
        routes.document_ai.cover_builder,
        "build",
        lambda profile, job: "cover letter text",
    )

    client.get("/")

    generate_response = client.get("/generate/0")
    assert generate_response.status_code == 200
    assert b"Job not found." not in generate_response.data

    coverletter_response = client.get("/coverletter/0")
    assert coverletter_response.status_code == 200
    assert b"Job not found." not in coverletter_response.data
