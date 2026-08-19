import app.web.routes as routes
from app.search.v2.job import CanonicalJob
from app.search.v2.matching.result import MatchResult
from app.search.v2.ranking import RankedJob


def make_ranked_job(url):
    job = CanonicalJob(
        title="Security Engineer",
        company="Example",
        location="Helsinki",
        url=url,
        source="Example",
    )
    match = MatchResult(job_id=url, score=80.0)
    return RankedJob(job=job, match=match)


def _reset_cache():
    routes._v2_search_cache["jobs"] = None
    routes._v2_search_cache["fetched_at"] = 0.0
    routes._v2_search_cache["service_factory"] = None


class CountingV2Service:
    """
    A fake V2 service that counts how many times .search() is actually
    called - the whole point of the cache is that a real search
    shouldn't run again for a repeat dashboard visit within the TTL.
    """

    call_count = 0

    def __init__(self, jobs):
        self._jobs = jobs

    def search(self, limit=50):
        CountingV2Service.call_count += 1
        return self._jobs


def test_repeat_dashboard_loads_reuse_cached_results_within_the_ttl(
    monkeypatch,
):
    """
    Regression test for the dashboard-slowness fix: two calls to
    _search_jobs() close together, using the same create_v2_service
    reference, must only perform one real search - the second is
    served from cache, not a fresh crawl-delay-bound search.
    """

    _reset_cache()
    CountingV2Service.call_count = 0

    jobs = [make_ranked_job("https://example.test/jobs/1")]

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: CountingV2Service(jobs),
    )

    first = routes._search_jobs(profile={})
    second = routes._search_jobs(profile={})

    assert CountingV2Service.call_count == 1
    assert first is second


def test_force_refresh_always_bypasses_the_cache(monkeypatch):
    """
    Regression test: the explicit "Search Jobs" action (/search) must
    always get fresh results, never a cached copy - that's the whole
    point of the user clicking it.
    """

    _reset_cache()
    CountingV2Service.call_count = 0

    jobs = [make_ranked_job("https://example.test/jobs/1")]

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: CountingV2Service(jobs),
    )

    routes._search_jobs(profile={})
    routes._search_jobs(profile={}, force_refresh=True)

    assert CountingV2Service.call_count == 2


def test_cache_expires_after_the_ttl(monkeypatch):
    _reset_cache()
    CountingV2Service.call_count = 0

    jobs = [make_ranked_job("https://example.test/jobs/1")]

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)
    monkeypatch.setattr(
        routes,
        "create_v2_service",
        lambda profile=None: CountingV2Service(jobs),
    )

    routes._search_jobs(profile={})

    # Simulate the cache having been filled long enough ago that it's
    # past its TTL, without actually waiting in real time.
    routes._v2_search_cache["fetched_at"] -= (
        routes._V2_SEARCH_CACHE_TTL_SECONDS + 1
    )

    routes._search_jobs(profile={})

    assert CountingV2Service.call_count == 2


def test_cache_does_not_leak_between_different_search_service_factories(
    monkeypatch,
):
    """
    Regression test for a real bug found while building this cache: it
    must not serve one caller's cached results to a different caller
    using a different create_v2_service - the exact scenario every
    test in this suite exercises via monkeypatch, which the cache
    initially broke (8 unrelated tests started failing because the
    dashboard cache leaked one test's fake jobs into the next).
    """

    _reset_cache()

    jobs_a = [make_ranked_job("https://example.test/a")]
    jobs_b = [make_ranked_job("https://example.test/b")]

    monkeypatch.setattr(routes, "v2_enabled", lambda: True)

    monkeypatch.setattr(
        routes, "create_v2_service", lambda profile=None: CountingV2Service(jobs_a)
    )
    first = routes._search_jobs(profile={})

    monkeypatch.setattr(
        routes, "create_v2_service", lambda profile=None: CountingV2Service(jobs_b)
    )
    second = routes._search_jobs(profile={})

    assert first[0].url == "https://example.test/a"
    assert second[0].url == "https://example.test/b"
