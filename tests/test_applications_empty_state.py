import app.web.routes as routes


def _client(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(routes, "v2_enabled", lambda: False)

    from webapp import app

    return app.test_client()


def test_applications_page_guides_a_first_time_user_instead_of_a_bare_table(
    monkeypatch, tmp_path
):
    """
    A brand-new install (or a real, genuinely-empty applications table -
    the state confirmed live in data/careerpilot.db) previously rendered
    a table with headers and zero rows and no guidance at all. It should
    instead tell the user what to do next, matching the same
    "guide toward the next action" bar the dashboard's own empty state
    already meets.
    """

    client = _client(monkeypatch, tmp_path)

    response = client.get("/applications")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "haven't added an application yet" in body
    assert "<table" not in body
