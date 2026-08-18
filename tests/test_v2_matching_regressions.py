from app.search.v2.job import CanonicalJob
from app.search.v2.matching import JobMatcher
from app.search.v2.matching.signals import find_skill_matches, title_matches


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
