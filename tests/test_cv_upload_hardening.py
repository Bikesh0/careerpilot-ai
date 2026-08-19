import hashlib
import io
import os
import time

import app.web.routes as routes


def _profile_hash(absolute_path):
    with open(absolute_path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def test_master_profile_is_never_modified_by_a_cv_upload(monkeypatch, tmp_path):
    """
    Regression/safety test for the work order's "master profile
    protection" requirement: uploading and extracting a CV - however
    the extraction turns out - must never write to the real
    profiles/profile.json (the single source of truth for matching,
    resumes, and cover letters).
    """

    profile_path = os.path.abspath("profiles/profile.json")
    before = _profile_hash(profile_path)

    monkeypatch.chdir(tmp_path)
    routes._reset_upload_rate_limit()

    monkeypatch.setattr(
        routes.cv_parser, "parse", lambda path: "Some CV text content."
    )
    monkeypatch.setattr(
        routes.profile_extractor,
        "extract",
        lambda text: {"name": "A Visitor", "skills": ["Something Else"]},
    )

    from webapp import app

    client = app.test_client()

    data = {
        "cv_file": (io.BytesIO(b"fake docx content"), "visitor_cv.docx"),
    }

    response = client.post(
        "/settings/upload-cv",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    after = _profile_hash(profile_path)

    assert before == after


def test_old_uploads_are_cleaned_up_past_the_retention_window(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)

    old_dir = tmp_path / "data" / "cv_uploads"
    old_dir.mkdir(parents=True)

    old_file = old_dir / "stale.docx"
    old_file.write_bytes(b"old upload")

    old_timestamp = time.time() - routes.CV_UPLOAD_RETENTION_SECONDS - 3600
    import os
    os.utime(old_file, (old_timestamp, old_timestamp))

    recent_file = old_dir / "recent.docx"
    recent_file.write_bytes(b"recent upload")

    monkeypatch.setattr(routes, "CV_UPLOAD_DIR", old_dir)

    routes._cleanup_old_uploads()

    assert not old_file.exists()
    assert recent_file.exists()


def test_upload_route_rate_limits_excessive_attempts(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    routes._reset_upload_rate_limit()
    monkeypatch.setattr(routes, "UPLOAD_RATE_LIMIT", 3)

    from webapp import app

    client = app.test_client()

    def _attempt():
        return client.post(
            "/settings/upload-cv",
            data={},
            content_type="multipart/form-data",
        )

    responses = [_attempt() for _ in range(4)]

    assert responses[-1].status_code == 429
    assert responses[0].status_code == 200

    routes._reset_upload_rate_limit()
