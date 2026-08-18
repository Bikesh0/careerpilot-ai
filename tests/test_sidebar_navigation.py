from webapp import app


def test_every_sidebar_link_resolves_without_a_404():
    """
    Regression test.

    templates/base.html's sidebar links to /, /search, /applications,
    /resume, /coverletter, /interview, and /settings. Four of those
    (/resume, /coverletter, /interview, /settings) had no matching
    Flask route at all, so every one of those links 404'd. /resume and
    /coverletter (bare, no job id) now redirect to the dashboard, since
    resume/cover-letter generation is inherently job-specific;
    /interview and /settings render their existing "Coming soon"
    placeholder templates.
    """

    client = app.test_client()

    for path in ("/interview", "/settings"):
        response = client.get(path)
        assert response.status_code == 200, path

    for path in ("/resume", "/coverletter"):
        response = client.get(path)
        assert response.status_code == 302, path
        assert response.headers["Location"] == "/"
