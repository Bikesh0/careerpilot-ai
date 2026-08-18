from app.search.sources.web_sources import DuunitoriSource, JoblySource


def test_is_same_site_accepts_relative_link_resolved_against_base():
    source = DuunitoriSource()
    url = "https://duunitori.fi/tyopaikat/tyo/security-engineer-1"

    assert source.is_same_site(url) is True


def test_is_same_site_rejects_absolute_link_to_a_different_domain():
    """Regression test.

    A scraped listing page can contain absolute hrefs pointing
    anywhere (ads, embedded widgets, compromised content). urljoin()
    leaves an absolute href untouched, so without an explicit domain
    check the scraper would happily fetch and treat an attacker- or
    internally-controlled URL as a job posting detail page.
    """

    source = DuunitoriSource()
    url = "https://attacker.example/tyopaikat/tyo/fake"

    assert source.is_same_site(url) is False


def test_is_same_site_is_scoped_per_source():
    duunitori = DuunitoriSource()
    jobly = JoblySource()

    jobly_url = "https://www.jobly.fi/tyopaikka/security-engineer-1"

    assert duunitori.is_same_site(jobly_url) is False
    assert jobly.is_same_site(jobly_url) is True
