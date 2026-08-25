from app.search.sources.ashby_source import AshbySource


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _hoxhunt_payload():
    return {
        "jobs": [
            {
                "id": "abc-123",
                "title": "Security Engineer, SecOps",
                "descriptionPlain": (
                    "We are looking for a Security Engineer with "
                    "Python and Kubernetes experience to join our "
                    "SecOps team."
                ),
                "descriptionHtml": (
                    "<p>We are looking for a Security Engineer with "
                    "Python and Kubernetes experience.</p>"
                ),
                "location": "Helsinki, Finland",
                "jobUrl": "https://jobs.ashbyhq.com/hoxhunt/abc-123",
                "publishedAt": "2026-08-01T09:00:00Z",
            }
        ]
    }


def test_ashby_source_reads_description_plain_not_description(monkeypatch):
    """
    Ashby's job-board list endpoint has no "description" key at all -
    only "descriptionPlain" (and an HTML twin, "descriptionHtml").
    Reading the wrong key silently produced an empty description for
    every Ashby job, which meant every Ashby-sourced job's skill-gap
    analysis fell back to matching on the title alone.
    """

    def mock_get(url, timeout):
        return MockResponse(_hoxhunt_payload())

    monkeypatch.setattr(
        "app.search.sources.ashby_source.requests.get",
        mock_get,
    )

    jobs = AshbySource().search()

    # One matching posting per board (mock_get returns the same payload
    # for every board.hoxhunt/Reaktor/mapbox call) - the field-name bug
    # under test doesn't depend on how many boards are configured.
    assert jobs
    for job in jobs:
        assert job.description
        assert "Kubernetes" in job.description
        assert "Python" in job.description
