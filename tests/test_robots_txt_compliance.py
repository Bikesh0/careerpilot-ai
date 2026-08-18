from app.search.manager import SearchManager
from app.search.sources.web_sources import JoblySource
from app.search.v2.registry import get_source_names


def test_duunitori_is_not_registered_in_v2():
    """
    Regression test.

    duunitori.fi/robots.txt disallows the generic "*" user-agent group
    (Disallow: /), and this scraper identifies itself with a spoofed
    browser User-Agent rather than one of the site's specifically
    allowlisted crawlers. DuunitoriSource itself is untouched and still
    tested in isolation (see test_duunitori_source.py,
    test_source_domain_guard.py) - only its registration was removed,
    so a V2 search must never include it as an active source again
    without a deliberate decision to re-add it.
    """

    assert "Duunitori" not in get_source_names()


def test_duunitori_is_not_registered_in_v1_search_manager():
    manager = SearchManager()

    searcher_class_names = [
        searcher.__class__.__name__
        for searcher in manager.searchers
    ]

    assert "DuunitoriSource" not in searcher_class_names


def test_jobly_get_page_honors_crawl_delay(monkeypatch):
    """
    Regression test.

    jobly.fi/robots.txt specifies "Crawl-delay: 10" for the generic
    user-agent group. JoblySource.get_page() must pause for that long
    after every request, not just fetch immediately.
    """

    sleep_calls = []

    monkeypatch.setattr(
        "app.search.sources.web_sources.time.sleep",
        lambda seconds: sleep_calls.append(seconds),
    )

    class FakeResponse:
        text = "<html></html>"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "app.search.sources.web_sources.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    source = JoblySource()
    html = source.get_page("https://www.jobly.fi/tyopaikat")

    assert html == "<html></html>"
    assert sleep_calls == [JoblySource.CRAWL_DELAY_SECONDS]
