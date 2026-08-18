import re
from typing import Iterable, List


def normalize_skill(value: str) -> str:
    value = str(value or "").strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[/_-]+", " ", value)
    value = re.sub(r"[^a-z0-9+#. ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokenize(value: str) -> list[str]:
    normalized = normalize_skill(value)
    return normalized.split() if normalized else []


def _contains_term(text: str, term: str) -> bool:
    """Match a phrase by normalized word boundaries, not substrings."""
    text_tokens = _tokenize(text)
    term_tokens = _tokenize(term)

    if not text_tokens or not term_tokens:
        return False

    width = len(term_tokens)
    return any(
        text_tokens[i:i + width] == term_tokens
        for i in range(len(text_tokens) - width + 1)
    )


def extract_text(job) -> str:
    parts = [
        getattr(job, "title", ""),
        getattr(job, "description", ""),
        getattr(job, "company", ""),
        getattr(job, "location", ""),
        " ".join(getattr(job, "skills", []) or []),
        " ".join(getattr(job, "tags", []) or []),
    ]
    return " ".join(str(part or "") for part in parts)


def find_skill_matches(job, profile_skills: Iterable[str]):
    text = extract_text(job)
    matched: List[str] = []
    missing: List[str] = []
    seen = set()

    for skill in profile_skills or []:
        normalized = normalize_skill(skill)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)

        if _contains_term(text, normalized):
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def title_matches(job, target_titles: Iterable[str]) -> List[str]:
    title = str(getattr(job, "title", "") or "")
    matches = []

    for target in target_titles or []:
        normalized = normalize_skill(target)
        if normalized and _contains_term(title, normalized):
            matches.append(target)

    return matches


def location_matches(job, target_locations: Iterable[str]) -> List[str]:
    location = str(getattr(job, "location", "") or "")
    matches = []

    for target in target_locations or []:
        normalized = normalize_skill(target)
        if normalized and _contains_term(location, normalized):
            matches.append(target)

    return matches


# Ported from app.ai.matcher.JobMatcher._extract_required_experience -
# same patterns, verified against real postings in that matcher before
# being carried over here.
_EXPERIENCE_YEAR_PATTERNS = [
    r"(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience",
    r"minimum\s+of\s+(\d+)\s+years?",
    r"at\s+least\s+(\d+)\s+years?",
    r"(\d+)\s*-\s*\d+\s+years?\s+(?:of\s+)?experience",
    r"(\d+)\s*\+\s*years?",
]


def extract_required_experience_years(text: str):
    """
    Return the highest number of years of experience mentioned in
    `text` (e.g. "5+ years of experience", "at least 3 years"), or
    None if no such phrase is found.
    """

    text = str(text or "")
    matches = []

    for pattern in _EXPERIENCE_YEAR_PATTERNS:
        for value in re.findall(pattern, text, flags=re.IGNORECASE):
            try:
                matches.append(int(value))
            except (TypeError, ValueError):
                continue

    return max(matches) if matches else None
