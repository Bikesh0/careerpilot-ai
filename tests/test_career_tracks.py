from app.ai.career_profile import build_career_profile
from app.ai.career_tracks import CAREER_TRACKS, classify_job_family, rank_career_tracks


class FakeJob:
    def __init__(self, title="", description=""):
        self.title = title
        self.description = description


def test_every_track_skill_key_is_a_real_catalog_entry():
    """
    Regression guard: CAREER_TRACKS is hand-curated independently of
    SKILL_CATALOG, so a typo'd or renamed skill_key would otherwise
    silently vanish from every ranking rather than raising anywhere.
    """

    from app.ai.skill_gap import SKILL_CATALOG

    for track in CAREER_TRACKS.values():
        for skill_key in track["skill_keys"]:
            assert skill_key in SKILL_CATALOG, skill_key


def test_ranking_puts_the_strongest_evidenced_track_first():
    profile = {
        "skills": ["Networking", "Firewall", "IDS/IPS", "Linux"],
        "experience": [
            {"title": "IDS/Firewall", "description": "Configured firewall and IDS, monitored network traffic."}
        ],
        "certifications": [],
    }

    career_profile = build_career_profile(profile)
    ranked = rank_career_tracks(career_profile)

    assert ranked[0]["key"] == "network_security"
    assert ranked[0]["profile_fit"] >= ranked[-1]["profile_fit"]


def test_a_skill_with_no_evidence_at_all_scores_lower_than_a_bare_claim():
    with_claim = build_career_profile(
        {"skills": ["AWS"], "experience": [], "certifications": []}
    )
    without_claim = build_career_profile(
        {"skills": [], "experience": [], "certifications": []}
    )

    ranked_with = rank_career_tracks(with_claim)
    ranked_without = rank_career_tracks(without_claim)

    cloud_with = next(t for t in ranked_with if t["key"] == "cloud_security")
    cloud_without = next(t for t in ranked_without if t["key"] == "cloud_security")

    assert cloud_with["profile_fit"] > cloud_without["profile_fit"]


def test_market_signal_is_none_without_job_data_not_a_misleading_zero():
    career_profile = build_career_profile(
        {"skills": [], "experience": [], "certifications": []}
    )

    ranked = rank_career_tracks(career_profile, job_texts=None)

    assert all(track["market_signal"] is None for track in ranked)


def test_market_signal_reflects_real_job_text_frequency():
    career_profile = build_career_profile(
        {"skills": [], "experience": [], "certifications": []}
    )

    job_texts = [
        "SOC Analyst - SIEM, incident response, Splunk required.",
        "Cloud Engineer - AWS, Azure, IAM.",
        "SOC Analyst - SIEM and detection required.",
    ]

    ranked = rank_career_tracks(career_profile, job_texts=job_texts)
    soc = next(t for t in ranked if t["key"] == "soc_security_operations")
    devsecops = next(t for t in ranked if t["key"] == "devsecops")

    assert soc["market_signal"] > devsecops["market_signal"]


# =============================================================
# Job-side classification: primary/secondary career family
# =============================================================

def test_a_clearly_cloud_security_job_classifies_as_such():
    job = FakeJob(
        title="Cloud Security Engineer",
        description=(
            "Requirements: AWS, Azure, IAM, cloud security, "
            "infrastructure as code, terraform."
        ),
    )

    result = classify_job_family(job)

    assert result["primary"]["key"] == "cloud_security"


def test_a_job_spanning_two_families_gets_a_secondary_classification():
    job = FakeJob(
        title="SOC Analyst",
        description=(
            "Requirements: SIEM, Splunk, incident response, log "
            "analysis, networking."
        ),
    )

    result = classify_job_family(job)

    assert result["primary"]["key"] == "soc_security_operations"
    assert result["secondary"] is not None
    assert result["secondary"]["key"] != result["primary"]["key"]


def test_an_unrelated_job_gets_no_family_forced_on_it():
    job = FakeJob(
        title="Front Desk Coordinator",
        description="Answer phones and greet visitors.",
    )

    result = classify_job_family(job)

    assert result["primary"] is None
    assert result["secondary"] is None


def test_a_single_incidental_skill_mention_does_not_become_a_secondary_family():
    """
    Regression test: a posting that's overwhelmingly one family and
    only mentions one skill from an unrelated track must not pick up
    that track as a spurious "secondary" classification.
    """

    job = FakeJob(
        title="Cloud Security Engineer",
        description=(
            "Requirements: AWS, Azure, Google Cloud, cloud security, "
            "IAM, infrastructure as code. Basic Linux familiarity is a "
            "plus."
        ),
    )

    result = classify_job_family(job)

    assert result["primary"]["key"] == "cloud_security"
    if result["secondary"] is not None:
        assert result["secondary"]["coverage"] >= 34
