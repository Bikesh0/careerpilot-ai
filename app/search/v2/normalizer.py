from datetime import datetime

from .job import CanonicalJob


def _value(raw, name, default=""):
    if isinstance(raw, dict):
        return raw.get(name, default)
    return getattr(raw, name, default)


def _normalize_skills(skills_raw):
    """Normalize skills while preserving first-seen spelling and order."""

    if not skills_raw:
        return []

    if isinstance(skills_raw, str):
        skills_raw = [skills_raw]

    skills = []
    seen = set()

    try:
        for skill in skills_raw:
            cleaned = str(skill).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            skills.append(cleaned)

    except TypeError:
        return []

    return skills


def _normalize_tags(tags_raw):
    """Normalize tags while preserving first-seen spelling and order."""

    if not tags_raw:
        return []

    if isinstance(tags_raw, str):
        tags_raw = [tags_raw]

    tags = []
    seen = set()

    try:
        for tag in tags_raw:
            cleaned = str(tag).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            tags.append(cleaned)

    except TypeError:
        return []

    return tags


def _normalize_posted_at(value):
    if isinstance(value, datetime):
        return value

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None


def _normalize_remote(raw):
    workplace = str(
        _value(raw, "workplace_type", "") or ""
    ).strip().casefold()

    if workplace in {
        "remote",
        "fully remote",
        "remote work",
    }:
        return True

    if workplace in {
        "onsite",
        "on-site",
        "office",
        "hybrid",
    }:
        return False

    return None


def normalize_job(raw) -> CanonicalJob:
    """Convert V1 Job objects or compatible dictionaries to CanonicalJob."""

    return CanonicalJob(
        title=str(
            _value(raw, "title", "") or ""
        ).strip(),

        company=str(
            _value(raw, "company", "") or ""
        ).strip(),

        location=str(
            _value(raw, "location", "") or ""
        ).strip(),

        url=str(
            _value(raw, "url", "") or ""
        ).strip(),

        source=str(
            _value(raw, "source", "unknown") or "unknown"
        ).strip(),

        description=str(
            _value(raw, "description", "") or ""
        ).strip(),

        external_id=str(
            _value(raw, "source_id", "") or ""
        ).strip() or None,

        employment_type=str(
            _value(raw, "employment_type", "") or ""
        ).strip() or None,

        remote=_normalize_remote(raw),

        salary_min=_value(raw, "salary_min", None),

        salary_max=_value(raw, "salary_max", None),

        salary_currency=_value(
            raw,
            "salary_currency",
            None,
        ),

        posted_at=_normalize_posted_at(
            _value(raw, "posted_at", None)
        ),

        skills=_normalize_skills(
            _value(raw, "skills", [])
        ),

        tags=_normalize_tags(
            _value(raw, "tags", [])
        ),
    )


def normalize_jobs(jobs) -> list[CanonicalJob]:
    normalized = []

    for raw in jobs or []:
        try:
            job = normalize_job(raw)

            if job.title and job.url:
                normalized.append(job)

        except Exception:
            continue

    return normalized