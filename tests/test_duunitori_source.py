from app.search.sources.web_sources import DuunitoriSource


def test_parse_job_detail_prefers_h1_over_json_ld_taxonomy_title():
    """Regression test.

    Duunitori's JobPosting JSON-LD "title" field holds an internal
    occupation-taxonomy slug (e.g. "tietoturva-asiantuntija") rather
    than the actual posted job title. The real title is only reliably
    available in the page's <h1>. Trusting the JSON-LD field alone
    made most Duunitori postings score title_score=0 during matching,
    even for genuinely relevant security roles.
    """

    html = """
    <html>
      <body>
        <h1>Staff Security Engineer</h1>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": "tietoturva-asiantuntija",
            "description": "We are looking for a security engineer.",
            "hiringOrganization": {"name": "Example Oy"},
            "jobLocation": {
                "address": {"addressLocality": "Helsinki"}
            }
        }
        </script>
      </body>
    </html>
    """

    details = DuunitoriSource().parse_job_detail(
        html,
        fallback_title="tietoturva-asiantuntija",
    )

    assert details["title"] == "Staff Security Engineer"
    assert details["company"] == "Example Oy"
    assert details["location"] == "Helsinki"


def test_parse_job_detail_falls_back_to_json_ld_title_without_h1():
    html = """
    <html>
      <body>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": "Security Engineer",
            "description": "Role description.",
            "hiringOrganization": {"name": "Example Oy"},
            "jobLocation": {
                "address": {"addressLocality": "Helsinki"}
            }
        }
        </script>
      </body>
    </html>
    """

    details = DuunitoriSource().parse_job_detail(
        html,
        fallback_title="fallback",
    )

    assert details["title"] == "Security Engineer"
