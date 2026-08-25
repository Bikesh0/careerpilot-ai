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


def test_analyze_route_shows_ready_to_apply_banner_when_fully_matched(
    monkeypatch,
):
    """
    Regression test for the "ready to apply" / "one next best action"
    UX requirement: a job the candidate already fully matches on
    required skills should tell them so plainly on the page.
    """

    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            title="Linux Engineer",
            description="Requirements: Linux experience required.",
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")

    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Ready to apply" in body
    assert "Apply now" in body


def test_analyze_route_shows_already_demonstrated_skills_first(monkeypatch):
    """
    Regression test for the mission's "do not simply display a missing
    skills wall" requirement: a positive "You already demonstrate"
    section must exist and list matched skills, separate from the
    detailed required/nice-to-have gap breakdown below it.
    """

    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            description=(
                "Requirements: Linux and Python experience required.\n"
                "Nice to have: Docker is a plus.\n"
            ),
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert "You already demonstrate" in body
    demonstrate_idx = body.index("You already demonstrate")
    required_idx = body.index("<h3>Required skills</h3>")
    assert demonstrate_idx < required_idx

    chip_section = body[demonstrate_idx:required_idx]
    assert "sg-skill-chip" in chip_section
    assert "Linux" in chip_section


def test_analyze_route_clarifies_the_score_is_not_a_probability(monkeypatch):
    """
    Regression test for the mission requirement that a match score must
    never be presented as (or read as) a probability of getting an
    interview or the job.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    # The template wraps this sentence across a source line, so the raw
    # HTML contains a literal newline where a browser would render a
    # collapsed space - normalize whitespace before comparing.
    normalized = " ".join(body.lower().split())
    assert "neither one is a probability" in normalized


def test_analyze_route_shows_an_apply_link(monkeypatch):
    """
    Regression test: the Skill Gap analysis page is a real destination
    a candidate reviews before applying - it must have a clear Apply
    link to the real posting, not just the dashboard card.
    """

    job_url = "https://example.test/jobs/1"
    jobs = [make_ranked_job(job_url)]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert f'href="{job_url}"' in body
    assert "Apply" in body


def test_analyze_route_hides_internal_implementation_jargon(monkeypatch):
    """
    Regression test for the mission's UI-copy requirement: internal
    implementation details (module names, "deterministic", "zero
    AI-generated content" etc.) belong in docs/, not the product UI.
    """

    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert "How this works" not in body
    assert "hand-checked list" not in body
    assert "SKILL_CATALOG" not in body


def test_analyze_route_gives_an_honest_no_extraction_message_not_a_blank_no_skills_claim(
    monkeypatch,
):
    """
    Regression test for Phase 6's empty-state fix: when nothing in the
    curated catalog matched at all (analysis.summary.no_requirements_detected),
    the page must say extraction didn't find structured requirements -
    not the flatter, easy-to-misread "No required skills detected for
    this posting," which reads as "this job asks for nothing."
    """

    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            title="Front Desk Coordinator",
            description="Completely unrelated posting text with no catalog terms.",
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert "could be reliably extracted" in body.lower()
    assert "No required skills detected for this posting." not in body


def test_analyze_route_connects_a_missing_skill_recommendation_to_its_career_family(
    monkeypatch,
):
    """
    Regression test for Milestone 1's one remaining gap: a missing-skill
    recommendation must say which career family the job was classified
    into (already computed by app.ai.career_tracks.classify_job_family
    and already available to the template), not just show effort/
    priority in isolation. Verifies the actual rendered HTML, not just
    that the analysis dict carries the data.
    """

    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            title="Cloud Security Engineer",
            description=(
                "Requirements: AWS, IAM, cloud security, infrastructure "
                "as code required."
            ),
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "This role is classified as Cloud Security" in body
    assert "closing this gap directly supports that track." in body


def test_analyze_route_omits_the_career_family_sentence_when_no_family_applies(
    monkeypatch,
):
    """
    Negative-case counterpart to the test above: when
    classify_job_family() finds no primary family for a posting (e.g.
    it's unrelated to every catalog track), the career-family sentence
    must not appear anywhere on the page - no fake/default family
    invented, and the route must still render normally (200, no
    exception). Protects the "gracefully do nothing if no career
    family is available" requirement.
    """

    jobs = [
        make_ranked_job(
            "https://example.test/jobs/1",
            title="Front Desk Coordinator",
            description=(
                "Answer phones and greet visitors, manage the front "
                "desk calendar."
            ),
        )
    ]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/0")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "This role is classified as" not in body
    assert "closing this gap directly supports that track." not in body


def test_analyze_route_returns_404_for_unknown_job_id(monkeypatch):
    jobs = [make_ranked_job("https://example.test/jobs/1")]
    client = _client(monkeypatch, jobs)

    client.get("/")
    response = client.get("/analyze/99")

    assert response.status_code == 404
