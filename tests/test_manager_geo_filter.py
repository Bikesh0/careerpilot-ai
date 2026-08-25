from app.search.manager import SearchManager
from app.search.sources.greenhouse_source import GreenhouseSource


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_search_manager_excludes_confidently_non_european_jobs_by_default(
    monkeypatch,
):
    """
    Regression test for the product spec's geographic scope rule:
    "outside Europe excluded by default." A job whose location is a
    confidently-identified non-European country/city must not reach
    manager.latest_jobs at all - while a Finnish or unrecognized
    location must still pass through untouched.
    """

    payload = {
        "jobs": [
            {
                "id": 1,
                "title": "Security Engineer",
                "content": "Linux, SIEM, incident response.",
                "location": {"name": "Helsinki, Finland"},
                "absolute_url": "https://boards.greenhouse.io/x/jobs/1",
                "first_published": "2026-08-01T09:00:00Z",
            },
            {
                "id": 2,
                "title": "Security Engineer",
                "content": "Linux, SIEM, incident response.",
                "location": {"name": "San Francisco, United States"},
                "absolute_url": "https://boards.greenhouse.io/x/jobs/2",
                "first_published": "2026-08-01T09:00:00Z",
            },
        ]
    }

    monkeypatch.setattr(
        "app.search.sources.greenhouse_source.requests.get",
        lambda url, timeout: MockResponse(payload),
    )

    manager = SearchManager()
    manager.searchers = [GreenhouseSource()]
    discovered_jobs = manager.search_jobs()

    locations = [job.location for job in discovered_jobs]

    assert "Helsinki, Finland" in locations
    assert "San Francisco, United States" not in locations
