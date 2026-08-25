from app.ai.hiring_perspective import (
    DEVELOPING,
    EVIDENCE_NEEDED,
    STRONG,
    build_hiring_perspective,
)
from app.ai.skill_gap import analyze_skill_gap


class FakeJob:
    def __init__(self, title="", description="", company=""):
        self.title = title
        self.description = description
        self.company = company


def test_three_perspectives_are_returned_separately_never_collapsed():
    job = FakeJob(
        title="Cloud Security Engineer",
        description="Requirements: AWS and Kubernetes required.",
    )
    profile = {"skills": [], "experience": [], "certifications": []}

    analysis = analyze_skill_gap(profile, job)
    perspective = build_hiring_perspective(profile, job, analysis)

    assert set(perspective.keys()) == {"ats", "hr", "technical"}
    for view in perspective.values():
        assert "level" in view and "label" in view and "detail" in view


def test_ats_perspective_reflects_required_skill_coverage():
    job = FakeJob(description="Requirements: AWS and Kubernetes required.")
    profile = {
        "skills": ["AWS", "Kubernetes"],
        "experience": [],
        "certifications": [],
    }

    analysis = analyze_skill_gap(profile, job)
    perspective = build_hiring_perspective(profile, job, analysis)

    assert perspective["ats"]["level"] == STRONG


def test_technical_perspective_requires_stronger_evidence_than_a_bare_claim():
    """
    Regression test for the core distinction the spec asks for: a
    skill only in the bare skills list (no verified project, no
    experience entry) must not count as strong technical-manager
    evidence, even though it's enough to satisfy the ATS keyword view.
    """

    job = FakeJob(description="Requirements: Kubernetes required.")
    profile = {
        "skills": ["Kubernetes"],
        "experience": [],
        "certifications": [],
    }

    analysis = analyze_skill_gap(profile, job)
    perspective = build_hiring_perspective(profile, job, analysis)

    assert perspective["ats"]["level"] == STRONG
    assert perspective["technical"]["level"] == EVIDENCE_NEEDED


def test_technical_perspective_is_strong_when_backed_by_a_verified_project():
    job = FakeJob(description="Requirements: Kubernetes required.")
    profile = {"skills": [], "experience": [], "certifications": []}
    projects = [
        {"id": 1, "skill_key": "kubernetes", "skill_display": "Kubernetes",
         "title": "K8s lab", "status": "Verified"},
    ]

    analysis = analyze_skill_gap(
        profile, job, existing_projects=projects
    )
    perspective = build_hiring_perspective(profile, job, analysis)

    assert perspective["technical"]["level"] == STRONG


def test_hr_perspective_notes_experience_years_without_inventing_tenure():
    job = FakeJob(
        title="Security Engineer",
        description="Requires 5+ years of experience.",
    )
    profile = {
        "skills": [],
        "experience": [{"title": "Trainee", "description": "..."}],
        "certifications": [],
        "target_titles": ["Security Engineer"],
    }

    analysis = analyze_skill_gap(profile, job)
    perspective = build_hiring_perspective(profile, job, analysis)

    assert "5+ years" in perspective["hr"]["detail"]
    # Must never claim the candidate HAS 5 years - only that the
    # posting mentions it, and the user should review their own
    # entries.
    assert "you have 5" not in perspective["hr"]["detail"].lower()


def test_perspectives_report_no_data_rather_than_a_guess_when_nothing_extracted():
    job = FakeJob(title="Front Desk Coordinator", description="Answer phones.")
    profile = {"skills": [], "experience": [], "certifications": []}

    analysis = analyze_skill_gap(profile, job)
    perspective = build_hiring_perspective(profile, job, analysis)

    assert perspective["ats"]["level"] is None
    assert perspective["technical"]["level"] is None
