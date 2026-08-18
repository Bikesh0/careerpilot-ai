from datetime import datetime, timezone

from app.search.v2.job import CanonicalJob
from app.search.v2.ranking import JobRanker


def make_job(**overrides):
    values = {
        "title": "Security Engineer",
        "company": "Example Corp",
        "location": "Helsinki",
        "url": "https://example.test/jobs/1",
        "source": "Example",
    }
    values.update(overrides)
    return CanonicalJob(**values)


def test_rank_does_not_crash_when_posted_at_is_mixed_none_and_datetime():
    """Regression test.

    A previous ranker implementation broke ties using
    ``job.posted_at or ""``, which raised TypeError as soon as two
    equally scored jobs mixed a real ``datetime`` with a missing
    (``None``) posted date, since str and datetime are not orderable.
    """

    with_date = make_job(
        url="https://example.test/jobs/1",
        posted_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )
    without_date = make_job(
        url="https://example.test/jobs/2",
        posted_at=None,
    )

    ranker = JobRanker()

    ranked = ranker.rank([with_date, without_date])

    assert [item.job.url for item in ranked] == [
        with_date.url,
        without_date.url,
    ]


def test_rank_assigns_sequential_rank_starting_at_one():
    jobs = [make_job(url=f"https://example.test/jobs/{i}") for i in range(3)]

    ranked = JobRanker().rank(jobs)

    assert [item.rank for item in ranked] == [1, 2, 3]


def test_rank_with_zero_limit_returns_empty_list():
    jobs = [make_job()]

    ranked = JobRanker().rank(jobs, limit=0)

    assert ranked == []

def test_rank_respects_positive_limit():
    jobs = [make_job(url=f"https://example.test/jobs/{i}") for i in range(5)]

    ranked = JobRanker().rank(jobs, limit=2)

    assert len(ranked) == 2


def test_ranked_job_to_dict_includes_rank_and_match_breakdown():
    job = make_job()

    ranked = JobRanker(
        profile_skills=["Linux"],
        target_titles=["Security Engineer"],
        target_locations=["Helsinki"],
    ).rank([job])[0]

    data = ranked.to_dict()

    assert data["rank"] == 1
    assert data["score"] == ranked.match.score
    assert data["match"]["title_score"] == ranked.match.title_score
    assert data["match"]["skill_score"] == ranked.match.skill_score


def test_title_match_ranks_above_unrelated_job():
    strong_title = make_job(
        url="https://example.test/jobs/strong-title",
        title="Security Engineer",
    )
    weak_title = make_job(
        url="https://example.test/jobs/weak-title",
        title="Warehouse Assistant",
    )

    ranker = JobRanker(target_titles=["Security Engineer"])

    ranked = ranker.rank([weak_title, strong_title])

    assert ranked[0].job.url == strong_title.url
