from app.ai.skill_gap import SKILL_CATALOG, analyze_skill_gap


class FakeJob:
    def __init__(self, title="", description="", company=""):
        self.title = title
        self.description = description
        self.company = company


def _entry(analysis, skill_display, group="required"):
    for item in analysis[group]:
        if item["skill"] == skill_display:
            return item
    return None


def test_required_and_nice_to_have_are_distinguished_per_sentence():
    """
    Regression test for the core UX requirement: a skill mentioned in a
    hedged sentence ("... is a plus", "nice to have", "preferred") must
    be classified separately from a skill mentioned as a plain
    requirement, even within the same job description.
    """

    job = FakeJob(
        title="Cloud Security Engineer",
        description=(
            "Requirements: strong experience with AWS and Terraform.\n"
            "Nice to have: Ansible experience is a plus.\n"
        ),
    )

    analysis = analyze_skill_gap({"skills": []}, job)

    required_names = {item["skill"] for item in analysis["required"]}
    nice_names = {item["skill"] for item in analysis["nice_to_have"]}

    assert "AWS" in required_names
    assert "Terraform" in required_names
    assert "Ansible" in nice_names
    assert "Ansible" not in required_names


def test_genuinely_absent_skill_is_detected_as_a_real_gap():
    """
    This is the specific gap both matchers (V1's app.ai.matcher and V2's
    app.search.v2.matching) have by design: their "missing_skills" means
    "profile skills the job text doesn't repeat", not "skills the job
    wants that the candidate doesn't have". A posting asking for
    Terraform, which never appears anywhere in the profile, must show up
    here as a missing required skill with a real recommendation attached
    - it was previously invisible to the application entirely.
    """

    profile = {
        "skills": ["Linux", "Python"],
        "experience": [],
        "certifications": [],
    }

    job = FakeJob(
        title="Platform Engineer",
        description="Requirements: Terraform experience is required.",
    )

    analysis = analyze_skill_gap(profile, job)
    terraform = _entry(analysis, "Terraform")

    assert terraform is not None
    assert terraform["status"] == "missing"
    assert terraform["priority"] == "required"
    assert terraform["recommendation"]["certifications"]
    assert terraform["recommendation"]["courses"]
    assert terraform["recommendation"]["projects"]
    assert terraform["recommendation"]["effort_days"] is not None


def test_matched_skill_only_in_skills_list_flags_weak_cv_evidence():
    """
    A skill the candidate lists but never demonstrates in an experience
    entry should be flagged for the CV-improvement section - without
    inventing an experience entry to "fix" it.
    """

    profile = {
        "skills": ["Splunk"],
        "experience": [
            {"title": "Helpdesk", "description": "Installed operating systems."}
        ],
        "certifications": [],
    }

    job = FakeJob(description="Requirements: Splunk experience required.")

    analysis = analyze_skill_gap(profile, job)
    splunk = _entry(analysis, "Splunk")

    assert splunk["status"] == "matched"
    assert "cv_note" in splunk
    assert "Splunk" in splunk["cv_note"]
    assert splunk["cv_note"] in analysis["cv_improvements"]


def test_matched_skill_with_experience_evidence_has_no_cv_note():
    """
    A skill that's both in the skills list and demonstrated in an
    experience entry is fully evidenced - no CV-improvement note should
    be raised for it.
    """

    profile = {
        "skills": ["Splunk"],
        "experience": [
            {
                "title": "SOC Trainee",
                "description": "Investigated alerts using Splunk daily.",
            }
        ],
        "certifications": [],
    }

    job = FakeJob(description="Requirements: Splunk experience required.")

    analysis = analyze_skill_gap(profile, job)
    splunk = _entry(analysis, "Splunk")

    assert splunk["status"] == "matched"
    assert "cv_note" not in splunk


def test_recommendations_never_claim_certifications_that_are_absent():
    """
    Some catalog entries (e.g. Git, VPN) deliberately have no real,
    well-known standalone certification - the catalog must leave that
    list empty rather than invent one, and the analysis output must
    faithfully reflect that (an empty list, not a fabricated entry).
    """

    assert SKILL_CATALOG["git"]["certifications"] == []

    profile = {"skills": [], "experience": [], "certifications": []}
    job = FakeJob(description="Requirements: Git experience required.")

    analysis = analyze_skill_gap(profile, job)
    git = _entry(analysis, "Git")

    assert git["recommendation"]["certifications"] == []


def test_priority_actions_lead_with_required_gaps_ordered_by_effort():
    """
    Regression test for the "prioritize by relevance and achievable
    effort/time" requirement: missing required skills must come before
    missing nice-to-have skills, and within each group the quickest
    realistic effort must come first.
    """

    profile = {"skills": [], "experience": [], "certifications": []}

    # Git: 1-3 days. Kubernetes: 7-14 days. Both required.
    # Docker (nice-to-have): 3-5 days.
    job = FakeJob(
        description=(
            "Requirements: Kubernetes and Git experience required.\n"
            "Nice to have: Docker experience is a plus.\n"
        )
    )

    analysis = analyze_skill_gap(profile, job)
    ordered_skills = [item["skill"] for item in analysis["priority_actions"]]

    assert ordered_skills.index("Git") < ordered_skills.index("Kubernetes")
    assert ordered_skills.index("Kubernetes") < ordered_skills.index("Docker")
    assert all(
        item["priority"] == "required"
        for item in analysis["priority_actions"][:2]
    )


def test_no_catalog_skills_detected_is_flagged_explicitly():
    """
    A posting with no recognizable catalog skills should say so clearly
    instead of silently implying 100% readiness with zero requirements.
    """

    job = FakeJob(title="Office Manager", description="Manage the office.")

    analysis = analyze_skill_gap({"skills": []}, job)

    assert analysis["summary"]["no_requirements_detected"] is True
    assert analysis["required"] == []
    assert analysis["nice_to_have"] == []


def test_readiness_percent_reflects_required_skill_coverage():
    profile = {
        "skills": ["Linux", "Python"],
        "experience": [],
        "certifications": [],
    }

    job = FakeJob(
        description=(
            "Requirements: Linux, Python, and Terraform are required."
        )
    )

    analysis = analyze_skill_gap(profile, job)

    assert analysis["summary"]["required_total"] == 3
    assert analysis["summary"]["required_matched"] == 2
    assert analysis["summary"]["readiness_percent"] == 67


def test_trailing_sentence_punctuation_does_not_hide_a_skill_mention():
    """
    Regression test: real job postings almost always end a requirement
    sentence with a period immediately after the skill name ("...
    experience with Terraform."). The word-boundary tokenizer must strip
    that punctuation before comparing tokens, or a token like
    "terraform." never equals the alias "terraform" and the mention is
    silently missed.
    """

    job = FakeJob(description="Requirements: experience with Terraform.")

    analysis = analyze_skill_gap({"skills": []}, job)
    terraform = _entry(analysis, "Terraform")

    assert terraform is not None
    assert terraform["status"] == "missing"
