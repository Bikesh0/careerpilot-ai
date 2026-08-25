from app.ai.career_profile import (
    BUILT,
    CERTIFIED,
    KNOWS,
    PRACTICED,
    PROFESSIONAL_EXPERIENCE,
    STUDIED,
    build_career_profile,
)


def _skill(result, name):
    for entry in result["skills"]:
        if entry["skill"] == name:
            return entry
    return None


def test_skill_with_no_other_signal_is_knows_only():
    profile = {"skills": ["Kubernetes"], "experience": [], "certifications": []}

    result = build_career_profile(profile)
    kubernetes = _skill(result, "Kubernetes")

    assert kubernetes["tiers"] == [KNOWS]


def test_skill_mentioned_in_experience_is_professional_experience():
    profile = {
        "skills": ["Linux"],
        "experience": [
            {"title": "Trainee", "description": "Worked with Linux daily."}
        ],
        "certifications": [],
    }

    result = build_career_profile(profile)
    linux = _skill(result, "Linux")

    assert PROFESSIONAL_EXPERIENCE in linux["tiers"]


def test_skill_in_certifications_is_certified():
    profile = {
        "skills": ["AWS"],
        "experience": [],
        "certifications": ["AWS Cloud Practitioner"],
    }

    result = build_career_profile(profile)
    aws = _skill(result, "AWS")

    assert CERTIFIED in aws["tiers"]


def test_skill_in_education_text_is_studied():
    profile = {
        "skills": ["Splunk"],
        "experience": [],
        "education": [{"degree": "Cyber Security (Splunk labs included)"}],
        "certifications": [],
    }

    result = build_career_profile(profile)
    splunk = _skill(result, "Splunk")

    assert STUDIED in splunk["tiers"]


def test_verified_project_skill_is_built():
    profile = {"skills": ["Kubernetes"], "experience": [], "certifications": []}

    result = build_career_profile(
        profile, verified_skill_keys={"kubernetes"}
    )
    kubernetes = _skill(result, "Kubernetes")

    assert BUILT in kubernetes["tiers"]


def test_in_progress_project_skill_is_practiced_not_built():
    """
    Regression test for the product spec's explicit distinction: a
    project underway is real effort, but not the same claim as a
    Verified, produced piece of evidence - PRACTICED must never be
    conflated with BUILT.
    """

    profile = {"skills": ["Kubernetes"], "experience": [], "certifications": []}
    projects = [
        {
            "id": 1,
            "skill_key": "kubernetes",
            "skill_display": "Kubernetes",
            "title": "K8s lab",
            "status": "In Progress",
        }
    ]

    result = build_career_profile(profile, projects=projects)
    kubernetes = _skill(result, "Kubernetes")

    assert PRACTICED in kubernetes["tiers"]
    assert BUILT not in kubernetes["tiers"]


def test_skill_can_carry_multiple_tiers_at_once():
    profile = {
        "skills": ["AWS"],
        "experience": [
            {"title": "Cloud Intern", "description": "Deployed workloads on AWS."}
        ],
        "certifications": ["AWS Cloud Practitioner"],
    }

    result = build_career_profile(profile)
    aws = _skill(result, "AWS")

    assert PROFESSIONAL_EXPERIENCE in aws["tiers"]
    assert CERTIFIED in aws["tiers"]
    assert aws["headline_tier"] == PROFESSIONAL_EXPERIENCE


def test_continuity_lists_in_progress_and_verified_projects_separately():
    profile = {"skills": [], "experience": [], "certifications": []}
    projects = [
        {"id": 1, "skill_key": "kubernetes", "skill_display": "Kubernetes",
         "title": "K8s lab", "status": "In Progress"},
        {"id": 2, "skill_key": "terraform", "skill_display": "Terraform",
         "title": "Terraform lab", "status": "Verified"},
    ]

    result = build_career_profile(profile, projects=projects)

    assert len(result["continuity"]["in_progress"]) == 1
    assert result["continuity"]["in_progress"][0]["skill_display"] == "Kubernetes"
    assert len(result["continuity"]["recently_built"]) == 1
    assert result["continuity"]["recently_built"][0]["skill_display"] == "Terraform"


def test_verified_project_surfaces_even_for_a_skill_not_in_the_skills_list():
    """
    Mirrors app/ai/cv_strength.py's existing precedent: real, produced
    evidence (a Verified project) must be visible even if the profile's
    declared skills list hasn't caught up to name it explicitly - it's
    simply not represented as a per-skill tier entry in that case,
    since there's no skill string to attach it to, but it's not lost
    either (it still appears in continuity.recently_built).
    """

    profile = {"skills": [], "experience": [], "certifications": []}
    projects = [
        {"id": 1, "skill_key": "kubernetes", "skill_display": "Kubernetes",
         "title": "K8s lab", "status": "Verified"},
    ]

    result = build_career_profile(
        profile, verified_skill_keys={"kubernetes"}, projects=projects
    )

    assert result["skills"] == []
    assert result["continuity"]["recently_built"][0]["skill_display"] == "Kubernetes"
