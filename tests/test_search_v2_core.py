from app.models.job import Job
from app.search.v2.dedupe import deduplicate_jobs
from app.search.v2.job import CanonicalJob
from app.search.v2.normalizer import normalize_job


def test_normalize_job_preserves_v1_fields():
    raw_job = Job(
        title="Security Engineer",
        company="Example Corp",
        location="Helsinki",
        url="https://example.test/jobs/1",
        description="Linux and SIEM",
        source="Example",
        source_id="external-1",
        posted_at="2026-08-01T09:00:00Z",
        workplace_type="Remote",
        skills=["Linux", "SIEM"],
    )

    normalized = normalize_job(raw_job)

    assert normalized.title == raw_job.title
    assert normalized.external_id == "external-1"
    assert normalized.remote is True
    assert normalized.posted_at.isoformat() == "2026-08-01T09:00:00+00:00"
    assert normalized.skills == ["Linux", "SIEM"]


def test_deduplicate_jobs_prefers_source_external_id():
    first = CanonicalJob(
        title="Security Engineer",
        company="Example Corp",
        location="Helsinki",
        url="https://example.test/jobs/1",
        source="Example",
        external_id="same-id",
    )
    duplicate = CanonicalJob(
        title="Security Engineer (updated)",
        company="Example Corp",
        location="Helsinki",
        url="https://example.test/jobs/1?updated=true",
        source="Example",
        external_id="same-id",
    )

    assert deduplicate_jobs([first, duplicate]) == [first]
