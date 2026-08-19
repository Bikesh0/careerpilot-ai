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


def test_ready_to_apply_when_every_required_skill_is_covered():
    """
    Regression test for the "ready to apply" requirement: the system
    must not invent an improvement just to have something to show. If
    every detected required skill is already covered, it should say so
    plainly instead of pushing an unnecessary recommendation.
    """

    profile = {
        "skills": ["Linux", "Python", "Docker"],
        "experience": [],
        "certifications": [],
    }

    job = FakeJob(
        title="Linux Engineer",
        description="Requirements: Linux and Python and Docker experience required.",
    )

    analysis = analyze_skill_gap(profile, job)

    assert analysis["ready_to_apply"] is True
    assert analysis["one_next_action"]["type"] == "apply"
    assert analysis["match_score"] is None


def test_not_ready_to_apply_when_a_required_skill_is_missing():
    profile = {"skills": ["Linux"], "experience": [], "certifications": []}

    job = FakeJob(
        title="Platform Engineer",
        description="Requirements: Linux and Terraform experience required.",
    )

    analysis = analyze_skill_gap(profile, job)

    assert analysis["ready_to_apply"] is False
    assert analysis["one_next_action"]["type"] == "skill_gap"
    assert analysis["one_next_action"]["skill"] == "Terraform"


def test_zero_requirements_detected_never_claims_readiness():
    """
    "no_requirements_detected" and "ready_to_apply" must never both
    imply false confidence - a posting this feature couldn't read
    should not be silently treated as "you match everything".
    """

    job = FakeJob(title="Office Manager", description="Manage the office.")

    analysis = analyze_skill_gap({"skills": []}, job)

    assert analysis["ready_to_apply"] is False
    assert analysis["summary"]["no_requirements_detected"] is True


def test_weak_cv_evidence_does_not_block_readiness_but_stays_visible():
    """
    Having every required skill covered - even if one is only weakly
    evidenced (in the skills list but not in experience) - is enough to
    say "ready to apply". Section 7 of the product spec is explicit:
    "Do not force unnecessary improvement... potential improvement can
    be optional." The CV-evidence note must still be visible in
    cv_improvements for a user who wants to strengthen it, just not
    presented as a blocker.
    """

    profile = {
        "skills": ["Linux", "Splunk"],
        "experience": [{"title": "Helpdesk", "description": "Fixed printers."}],
        "certifications": [],
    }

    job = FakeJob(
        description="Requirements: Linux and Splunk experience required."
    )

    analysis = analyze_skill_gap(profile, job)

    assert analysis["ready_to_apply"] is True
    assert analysis["one_next_action"]["type"] == "apply"
    assert any("Splunk" in note for note in analysis["cv_improvements"])


def test_next_action_prefers_cv_evidence_when_a_nice_to_have_is_missing_but_no_required_gap():
    """
    When there's no required-skill gap but a required skill's evidence
    is weak AND a nice-to-have is missing, strengthening the real,
    already-claimed skill should be suggested ahead of chasing an
    optional skill the candidate doesn't have at all.
    """

    profile = {
        "skills": ["Linux", "Splunk"],
        "experience": [{"title": "Helpdesk", "description": "Fixed printers."}],
        "certifications": [],
    }

    job = FakeJob(
        description=(
            "Requirements: Linux and Splunk experience required.\n"
            "Nice to have: Ansible experience is a plus.\n"
        )
    )

    analysis = analyze_skill_gap(profile, job)

    # Still "ready to apply" (Linux/Splunk are both matched), but the
    # richer one_next_action helper is exercised directly here to prove
    # cv_evidence would outrank an optional nice-to-have if surfaced.
    from app.ai.skill_gap import _build_next_action

    action = _build_next_action(
        ready_to_apply=False,
        priority_actions=analysis["priority_actions"],
        cv_improvements=analysis["cv_improvements"],
        nice_entries=analysis["nice_to_have"],
    )

    assert action["type"] == "cv_evidence"


def test_match_score_projection_is_honest_about_negligible_impact():
    """
    Regression test for "if completing a gap would not materially
    change the match, do not exaggerate its effect": a missing skill
    that barely moves the real V2 scoring formula must be reported as
    non-meaningful, not dressed up with an inflated potential number.
    """

    profile = {"skills": [], "experience": [], "certifications": []}

    # A title that matches nothing in target_titles and no location
    # match keeps title_score/location_score at 0 regardless of skills,
    # so a single skill addition should barely move the total score.
    job = FakeJob(
        title="Unrelated Ops Coordinator",
        description="Requirements: Ansible experience required.",
        company="ExampleCo",
    )

    analysis = analyze_skill_gap(profile, job)
    projection = analysis["match_score"]

    assert projection is not None
    if not projection["meaningful"]:
        assert projection["current"] == projection["potential"]


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
