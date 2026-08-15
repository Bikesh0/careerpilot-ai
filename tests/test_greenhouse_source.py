from app.search.sources.greenhouse_source import GreenhouseSource


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_greenhouse_source_maps_supported_job_fields(
    monkeypatch,
    greenhouse_payload,
):
    calls = []

    def mock_get(url, timeout):
        calls.append((url, timeout))
        return MockResponse(greenhouse_payload)

    monkeypatch.setattr(
        "app.search.sources.greenhouse_source.requests.get",
        mock_get,
    )

    jobs = GreenhouseSource().search()

    assert calls == [
        (
            "https://boards-api.greenhouse.io/v1/boards/aiven/jobs?content=true",
            20,
        )
    ]
    assert len(jobs) == 1

    job = jobs[0]
    assert job.title == "Junior Security Engineer"
    assert job.source == "Greenhouse"
    assert job.source_id == "4242"
    assert job.posted_at == "2026-08-01T09:00:00Z"
