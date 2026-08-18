import os

from app.search.v2.service import V2SearchService


def v2_enabled() -> bool:
    """Return whether V2 search is enabled."""

    value = os.getenv(
        "CAREERPILOT_SEARCH_V2",
        "0",
    )

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def create_v2_service(profile=None) -> V2SearchService:
    """Build a V2 search service from the user's profile."""

    profile = profile or {}

    return V2SearchService(
        profile_skills=profile.get(
            "skills",
            [],
        ),
        target_titles=profile.get(
            "target_titles",
            [],
        ),
        target_locations=profile.get(
            "target_locations",
            [],
        ),
    )