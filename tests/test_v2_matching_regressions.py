from app.search.v2.job import CanonicalJob
from app.search.v2.matching import JobMatcher
from app.search.v2.matching.signals import (
    extract_required_experience_years,
    find_skill_matches,
    title_matches,
)
from app.search.v2.ranking import JobRanker


def make_job(title="Security Engineer", description="AWS Linux networking"):
    return CanonicalJob(
        title=title,
        company="Example",
        location="Helsinki",
        url="https://example.test/job/1",
        source="test",
        description=description,
    )


def test_skill_matching_does_not_match_substrings():
    job = make_job(description="This role uses hardware and networks.")
    matched, missing = find_skill_matches(job, ["aws", "art"])
    assert "aws" not in matched
    assert "art" not in matched
    assert set(missing) == {"aws", "art"}


def test_title_matching_uses_word_boundaries():
    job = make_job(title="Senior Security Engineer")
    assert title_matches(job, ["Security Engineer"]) == ["Security Engineer"]
    assert title_matches(job, ["EngineerX"]) == []


def test_matcher_scores_title_and_skills():
    job = make_job(description="AWS Linux")
    result = JobMatcher(
        profile_skills=["AWS", "Linux", "Azure"],
        target_titles=["Security Engineer"],
        target_locations=["Helsinki"],
    ).score_job(job)

    assert result.title_score == 100.0
    assert result.location_score == 100.0
    assert result.skill_score == 66.67
    assert result.score > 70


# =========================================================
# Ported from the legacy app.ai.matcher.JobMatcher - see
# NEXT_TASKS.md Priority 1 / docs/MATCHING_AND_RANKING.md.
# =========================================================


def test_finnish_titled_job_matches_a_finnish_target_title():
    """
    Regression test for the Finnish-language title gap: V2's matcher
    has no hardcoded title vocabulary of its own (unlike V1's
    PRIMARY_TITLES), so recognizing a Finnish-titled posting depends
    entirely on the profile's target_titles containing the Finnish
    term - added to profiles/profile.json this session. This proves
    the underlying matching mechanism works for such a term; see
    tests/test_profile_integrity.py for confirmation the real profile
    file actually contains it.
    """

    job = make_job(
        title="Kyberturvallisuusasiantuntija",
        description="Tietoturva ja verkkoturvallisuus",
    )

    result = JobMatcher(
        target_titles=["Kyberturvallisuusasiantuntija"],
    ).score_job(job)

    assert result.title_score == 100.0
    assert "Target job title matched" in result.reasons


def test_excluded_title_terms_score_zero_and_are_flagged():
    """
    Regression test: ported from app.ai.matcher.JobMatcher.EXCLUDED_TITLE_TERMS.
    A posting for an obviously unrelated role (marketing, sales, HR,
    etc.) must never be presented as a match, regardless of any other
    signal - even a job with skills/location that would otherwise
    score well.
    """

    job = make_job(
        title="Senior Marketing Manager",
        description="AWS Linux Helsinki",
    )

    result = JobMatcher(
        profile_skills=["AWS", "Linux"],
        target_titles=["Marketing"],
        target_locations=["Helsinki"],
    ).score_job(job)

    assert result.excluded is True
    assert result.score == 0.0
    assert any("Excluded" in reason for reason in result.reasons)


def test_job_ranker_drops_excluded_jobs_entirely():
    """
    Regression test: excluded jobs must not merely rank last - they
    must not appear in the ranked output at all, matching the legacy
    matcher's behavior of skipping them before scoring.
    """

    relevant = make_job(
        title="Security Engineer",
        description="AWS Linux",
    )
    excluded = make_job(
        title="Sales Representative",
        description="AWS Linux",
    )
    excluded.url = "https://example.test/job/2"

    ranked = JobRanker(
        profile_skills=["AWS", "Linux"],
        target_titles=["Security Engineer"],
    ).rank([relevant, excluded])

    assert len(ranked) == 1
    assert ranked[0].job.title == "Security Engineer"


def test_extract_required_experience_years_finds_the_highest_figure():
    text = "We require at least 3 years of experience, ideally 7+ years."
    assert extract_required_experience_years(text) == 7
    assert extract_required_experience_years("no experience required") is None


def test_experience_requirement_penalizes_the_score():
    """
    Regression test: ported from
    app.ai.matcher.JobMatcher._experience_requirement_penalty. A
    posting explicitly requiring significant experience should score
    lower than an otherwise-identical posting that doesn't, since this
    matcher is used for an early-career candidate search.
    """

    demanding = make_job(
        title="Security Engineer",
        description="AWS Linux. Requires 7+ years of experience.",
    )
    ordinary = make_job(
        title="Security Engineer",
        description="AWS Linux.",
    )
    ordinary.url = "https://example.test/job/2"

    matcher = JobMatcher(
        profile_skills=["AWS", "Linux"],
        target_titles=["Security Engineer"],
    )

    demanding_result = matcher.score_job(demanding)
    ordinary_result = matcher.score_job(ordinary)

    assert demanding_result.score < ordinary_result.score
    assert any(
        "7+ years experience" in reason
        for reason in demanding_result.reasons
    )
