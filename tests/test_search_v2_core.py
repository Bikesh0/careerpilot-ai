
from app.models.job import Job
from app.search.v2.dedupe import deduplicate_jobs
from app.search.v2.job import CanonicalJob
from app.search.v2.normalizer import normalize_job


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


def test_normalized_title_collapses_case_and_whitespace():
    job = make_job(
        title="  SECURITY   Engineer  "
    )

    assert job.normalized_title() == "security engineer"


def test_normalized_company_removes_common_legal_suffix():
    job = make_job(
        company="Example Oy"
    )

    assert job.normalized_company() == "example"


def test_normalized_company_handles_oyj():
    job = make_job(
        company="Example Oyj"
    )

    assert job.normalized_company() == "example"


def test_normalized_location_is_case_insensitive():
    job = make_job(
        location="Helsinki, Finland"
    )

    assert job.normalized_location() == "helsinki"


def test_dedupe_key_uses_normalized_fields_without_external_id():
    first = make_job(
        title=" Security   Engineer ",
        company="Example Oy",
        location="HELSINKI, FINLAND",
        url="https://example.test/jobs/1",
    )

    second = make_job(
        title="SECURITY ENGINEER",
        company="Example",
        location="helsinki",
        url="https://different.example/jobs/999",
    )

    assert first.dedupe_key() == second.dedupe_key()


def test_deduplicate_jobs_collapses_normalized_duplicates():
    first = make_job(
        title="Security Engineer",
        company="Example Oy",
        location="Helsinki, Finland",
        url="https://example.test/jobs/1",
    )

    duplicate = make_job(
        title="  SECURITY   ENGINEER ",
        company="Example",
        location="helsinki",
        url="https://example.test/jobs/2",
    )

    result = deduplicate_jobs([first, duplicate])

    assert result == [first]


def test_deduplicate_jobs_keeps_different_locations():
    helsinki = make_job(
        location="Helsinki"
    )

    espoo = make_job(
        location="Espoo"
    )

    result = deduplicate_jobs([helsinki, espoo])

    assert result == [helsinki, espoo]


def test_deduplicate_jobs_keeps_different_external_ids():
    first = make_job(
        external_id="job-1"
    )

    second = make_job(
        external_id="job-2"
    )

    result = deduplicate_jobs([first, second])

    assert result == [first, second]


def test_deduplicate_jobs_external_id_is_scoped_to_source():
    first = make_job(
        source="Duunitori",
        external_id="123",
    )

    second = make_job(
        source="Jobly",
        external_id="123",
    )

    result = deduplicate_jobs([first, second])

    assert result == [first, second]


def test_normalize_job_deduplicates_skills():
    raw_job = {
        "title": "Security Engineer",
        "company": "Example",
        "location": "Helsinki",
        "url": "https://example.test/jobs/1",
        "source": "Example",
        "skills": [
            "Python",
            "python",
            " Linux ",
            "Linux",
        ],
    }

    normalized = normalize_job(raw_job)

    assert normalized.skills == [
        "Python",
        "Linux",
    ]


def test_normalize_job_accepts_string_skill():
    raw_job = {
        "title": "Security Engineer",
        "company": "Example",
        "location": "Helsinki",
        "url": "https://example.test/jobs/1",
        "source": "Example",
        "skills": "Python",
    }

    normalized = normalize_job(raw_job)

    assert normalized.skills == ["Python"]


def test_normalize_job_invalid_posted_at_becomes_none():
    raw_job = {
        "title": "Security Engineer",
        "company": "Example",
        "location": "Helsinki",
        "url": "https://example.test/jobs/1",
        "source": "Example",
        "posted_at": "not-a-date",
    }

    normalized = normalize_job(raw_job)

    assert normalized.posted_at is None


def test_normalize_job_maps_hybrid_to_non_remote():
    raw_job = {
        "title": "Security Engineer",
        "company": "Example",
        "location": "Helsinki",
        "url": "https://example.test/jobs/1",
        "source": "Example",
        "workplace_type": "Hybrid",
    }

    normalized = normalize_job(raw_job)

    assert normalized.remote is False

