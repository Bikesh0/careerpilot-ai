import io

import app.web.routes as routes
from webapp import app


def _client():
    return app.test_client()


def test_upload_cv_rejects_unsupported_file_extension():
    client = _client()

    response = client.post(
        "/settings/upload-cv",
        data={
            "cv_file": (io.BytesIO(b"not a real cv"), "resume.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Only PDF and DOCX files are supported." in response.data


def test_settings_page_hides_internal_implementation_details():
    """
    Regression test for the mission's UI-copy requirement: no file
    paths, module names, or "review-only preview" implementation
    jargon in user-facing copy - plain language only.
    """

    client = _client()
    response = client.get("/settings")
    body = response.get_data(as_text=True)

    assert "profiles/profile.json" not in body
    assert "profile.json" not in body
    assert "review-only preview" not in body


def test_upload_cv_requires_a_file():
    client = _client()

    response = client.post(
        "/settings/upload-cv",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Please choose a PDF or DOCX file." in response.data


def test_upload_cv_extracts_and_displays_profile_data_for_review(
    monkeypatch,
    tmp_path,
):
    """
    Regression test for the full CV-upload flow.

    Also verifies that a malicious client-supplied filename cannot
    escape the upload directory: the code never builds a path from
    uploaded_file.filename, only from a freshly generated UUID, so a
    filename like "../../evil.docx" can only affect the file's
    extension check, never where it's actually written.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        routes.cv_parser,
        "parse",
        lambda path: "Bikesh Shrestha\nSecurity Engineer\nLinux, Python",
    )
    monkeypatch.setattr(
        routes.profile_extractor,
        "extract",
        lambda cv_text: {
            "name": "Bikesh Shrestha",
            "skills": ["Linux", "Python"],
            "experience": [
                {"title": "Security Engineer", "company": "Example Corp"}
            ],
        },
    )

    client = _client()

    response = client.post(
        "/settings/upload-cv",
        data={
            "cv_file": (
                io.BytesIO(b"fake docx bytes"),
                "../../evil.docx",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    body = response.get_data(as_text=True)
    assert "Bikesh Shrestha" in body
    assert "Security Engineer" in body

    upload_dir = tmp_path / "data" / "cv_uploads"
    saved_files = list(upload_dir.glob("*.docx"))

    assert len(saved_files) == 1
    assert saved_files[0].parent == upload_dir
    assert saved_files[0].name != "evil.docx"


def test_upload_cv_degrades_gracefully_when_ai_extraction_fails(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        routes.cv_parser,
        "parse",
        lambda path: "some cv text",
    )

    def _raise(cv_text):
        raise RuntimeError(
            "CV extraction is unavailable (local Ollama did not respond)."
        )

    monkeypatch.setattr(routes.profile_extractor, "extract", _raise)

    client = _client()

    response = client.post(
        "/settings/upload-cv",
        data={
            "cv_file": (io.BytesIO(b"fake pdf bytes"), "resume.pdf"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"AI extraction is unavailable" in response.data
