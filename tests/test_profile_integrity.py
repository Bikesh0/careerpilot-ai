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


def test_profile_target_titles_include_finnish_terms():
    """
    Regression test for NEXT_TASKS.md Priority 1 (port V1's
    Finnish-language title terms into V2). V2's matcher has no
    hardcoded title vocabulary - unlike the legacy app.ai.matcher's
    PRIMARY_TITLES - so recognizing a Finnish-titled posting (e.g.
    Duunitori/Jobly listings with no English title text at all)
    depends entirely on profiles/profile.json's target_titles
    containing the Finnish equivalent. Without this, a real,
    genuinely relevant posting titled only in Finnish would score
    title_score=0 under V2, even though the legacy matcher would have
    recognized it.
    """

    with PROFILE_PATH.open(encoding="utf-8") as profile_file:
        data = json.load(profile_file)

    target_titles = [title.lower() for title in data["target_titles"]]

    assert any("kyberturvallisuus" in title for title in target_titles)
    assert any("tietoturva" in title for title in target_titles)
