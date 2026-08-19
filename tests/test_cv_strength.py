from app.ai.cv_strength import analyze_cv_strength


def _skill(analysis, name):
    for entry in analysis["skills"]:
        if entry["skill"] == name:
            return entry
    return None


def test_skill_demonstrated_in_two_experience_entries_is_advanced():
    profile = {
        "skills": ["Splunk"],
        "experience": [
            {"title": "SOC Trainee", "description": "Used Splunk daily for triage."},
            {"title": "Helpdesk", "description": "Also used Splunk for ticket logs."},
        ],
        "certifications": [],
    }

    analysis = analyze_cv_strength(profile)
    entry = _skill(analysis, "Splunk")

    assert entry["level"] == "Advanced"
    assert "multiple experience" in entry["evidence"]


def test_skill_backed_only_by_certification_says_so_honestly():
    """
    Regression test: a skill that reaches "Advanced" purely because a
    certification names it, with zero experience evidence, must say
    exactly that - not imply it was demonstrated on the job. This was a
    real bug found while building the feature: level and evidence text
    were computed independently and could contradict each other.
    """

    profile = {
        "skills": ["Terraform"],
        "experience": [
            {"title": "Helpdesk", "description": "Fixed printers and laptops."}
        ],
        "certifications": ["HashiCorp Certified: Terraform Associate"],
    }

    analysis = analyze_cv_strength(profile)
    entry = _skill(analysis, "Terraform")

    assert entry["level"] == "Advanced"
    assert "certification" in entry["evidence"]
    assert "not demonstrated" in entry["evidence"]


def test_skill_with_no_evidence_anywhere_is_basic_and_flagged():
    profile = {
        "skills": ["Ansible"],
        "experience": [
            {"title": "Helpdesk", "description": "Fixed printers and laptops."}
        ],
        "certifications": [],
    }

    analysis = analyze_cv_strength(profile)
    entry = _skill(analysis, "Ansible")

    assert entry["level"] == "Basic"
    assert any(
        weakness["category"] == "skill_evidence"
        and "Ansible" in weakness["message"]
        for weakness in analysis["weaknesses"]
    )


def test_experience_entry_with_no_numbers_is_flagged_as_unquantified():
    profile = {
        "skills": [],
        "experience": [
            {
                "title": "Support Engineer",
                "description": "Helped customers with various technical issues.",
            }
        ],
        "certifications": [],
    }

    analysis = analyze_cv_strength(profile)

    assert analysis["summary"]["experience_quantified"] == 0
    assert any(
        weakness["category"] == "quantification"
        for weakness in analysis["weaknesses"]
    )


def test_experience_entry_with_a_number_is_not_flagged():
    profile = {
        "skills": [],
        "experience": [
            {
                "title": "Support Engineer",
                "description": "Supported 200+ users and resolved tickets within 24 hours.",
            }
        ],
        "certifications": [],
    }

    analysis = analyze_cv_strength(profile)

    assert analysis["summary"]["experience_quantified"] == 1
    assert not any(
        weakness["category"] == "quantification"
        for weakness in analysis["weaknesses"]
    )


def test_weaknesses_are_capped_and_do_not_overwhelm_the_user():
    """
    Regression test for "do NOT overwhelm the user": even a profile with
    many simultaneous gaps must not dump every single one on the page.
    """

    profile = {
        "skills": [f"Skill{i}" for i in range(20)],
        "experience": [
            {"title": f"Role {i}", "description": "Did some things."}
            for i in range(10)
        ],
        "certifications": [],
    }

    analysis = analyze_cv_strength(profile)

    assert len(analysis["weaknesses"]) <= 5


def test_never_fabricates_a_certification_or_project():
    """
    The weakness message for missing certifications/projects must only
    ever suggest the user consider adding one - never claim they
    already have it, and never invent specific names.
    """

    profile = {"skills": [], "experience": [], "certifications": []}

    analysis = analyze_cv_strength(profile)
    messages = " ".join(w["message"] for w in analysis["weaknesses"]).lower()

    assert "actually completed" in messages
    assert "never label" in messages
    assert "you have completed" not in messages


def test_empty_profile_does_not_crash_and_returns_a_baseline_strength():
    analysis = analyze_cv_strength({})

    assert analysis["strengths"]
    assert analysis["summary"]["skills_total"] == 0
