from app.ai.matcher import JobMatcher
from app.models.job import Job
from app.search.filter import JobFilter


def test_filter_removes_duplicate_and_unrelated_jobs():
    relevant = Job(
        title="Junior Security Engineer",
        company="Example Corp",
        location="Helsinki",
        description="Linux, SIEM, and incident response.",
    )
    duplicate = Job(
        title="Junior Security Engineer",
        company="Example Corp",
        location="Espoo",
        description="A second listing record.",
    )
    unrelated = Job(
        title="Marketing Manager",
        company="Example Corp",
        location="Helsinki",
        description="Lead marketing campaigns.",
    )

    job_filter = JobFilter()
    unique_jobs = job_filter.remove_duplicates(
        [relevant, duplicate, unrelated]
    )

    assert unique_jobs == [relevant, unrelated]
    assert job_filter.cybersecurity_only(unique_jobs) == [relevant]


def test_matcher_ranks_security_role_and_excludes_marketing(
    candidate_profile,
):
    security_job = Job(
        title="Junior Security Engineer",
        company="Example Corp",
        location="Helsinki",
        description="Linux SIEM Python incident response.",
    )
    marketing_job = Job(
        title="Marketing Manager",
        company="Example Corp",
        location="Helsinki",
        description="Python is used for marketing analytics.",
    )

    ranked = JobMatcher().rank_jobs(
        [marketing_job, security_job],
        candidate_profile,
    )

    assert len(ranked) == 1
    assert ranked[0]["job"]["title"] == "Junior Security Engineer"
    assert ranked[0]["match_score"] >= 50
    assert {"python", "linux", "siem"} <= set(
        ranked[0]["matched_skills"]
    )
