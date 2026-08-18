import json
from pathlib import Path

from app.ai.profile_loader import ProfileLoader

PROFILE_PATH = (
    Path(__file__).resolve().parents[1] / "profiles" / "profile.json"
)


def test_profile_file_is_valid_json():
    """Regression test.

    profiles/profile.json was once saved with a wrapping Markdown code
    fence (```json ... ```), which made it fail json.load(). Because
    the web app's profile loading swallows exceptions and falls back
    to an empty profile, that corruption was silent: V2 matching ran
    with zero skills/titles/locations and nobody noticed from the
    dashboard alone.
    """

    with PROFILE_PATH.open(encoding="utf-8") as profile_file:
        data = json.load(profile_file)

    assert isinstance(data, dict)


def test_profile_has_required_matching_fields():
    with PROFILE_PATH.open(encoding="utf-8") as profile_file:
        data = json.load(profile_file)

    assert data.get("skills")
    assert data.get("target_titles")
    assert data.get("target_locations")


def test_profile_loader_loads_real_profile_successfully():
    profile = ProfileLoader().load()

    assert profile["skills"]
    assert profile["target_titles"]
    assert profile["target_locations"]
