def test_cv_strength_route_renders_with_the_real_profile():
    """
    Regression/integration test: Layer 1 (general CV strength) must be
    reachable on its own, independent of any job search or selected
    job - it uses only the real profile.json.
    """

    from webapp import app

    client = app.test_client()
    response = client.get("/cv-strength")

    assert response.status_code == 200

    body = response.get_data(as_text=True)
    assert "CV Strength" in body
    assert "Strengths" in body
    assert "Highest-value improvements" in body
    assert "Skill evidence" in body


def test_sidebar_links_to_cv_strength():
    """
    Checked via the /cv-strength page itself (which also extends
    base.html and renders the sidebar) rather than "/" - the dashboard
    route triggers a live job search fallback when V2 is disabled and
    no jobs are cached yet, which this test must not depend on.
    """

    from webapp import app

    client = app.test_client()
    response = client.get("/cv-strength")

    assert b'href="/cv-strength"' in response.data
