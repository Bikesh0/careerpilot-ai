import re
from typing import Iterable, List, Set


def normalize_skill(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def skill_set(values: Iterable[str]) -> Set[str]:
    return {
        normalize_skill(value)
        for value in values or []
        if normalize_skill(value)
    }


def extract_text(job) -> str:
    parts = [
        getattr(job, "title", ""),
        getattr(job, "description", ""),
        getattr(job, "company", ""),
        getattr(job, "location", ""),
    ]

    return " ".join(
        str(part or "")
        for part in parts
    ).lower()


def find_skill_matches(job, profile_skills: Iterable[str]):
    text = extract_text(job)

    matched = []
    missing = []

    for skill in profile_skills or []:
        normalized = normalize_skill(skill)

        if not normalized:
            continue

        if normalized in text:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def title_matches(job, target_titles: Iterable[str]) -> List[str]:
    title = str(
        getattr(job, "title", "")
        or ""
    ).lower()

    matches = []

    for target in target_titles or []:
        normalized = normalize_skill(target)

        if normalized and normalized in title:
            matches.append(target)

    return matches
