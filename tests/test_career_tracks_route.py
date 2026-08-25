from webapp import app


def test_cv_strength_page_shows_career_track_fit():
    client = app.test_client()
    response = client.get("/cv-strength")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Career track fit" in body
    assert "% profile fit" in body
