from datetime import datetime

from .job import CanonicalJob


def normalize_job(raw) -> CanonicalJob:
    """
    Convert the existing V1 Job model or a compatible object
    into the V2 canonical job representation.

    The normalizer preserves useful V1 fields instead of
    discarding them.
    """

    def value(name, default=""):
        result = getattr(raw, name, default)

        if result is None:
            return default

        return result

    source_id = str(
        value("source_id", "")
    ).strip()

    employment_type = str(
        value("employment_type", "")
    ).strip()

    workplace_type = str(
        value("workplace_type", "")
    ).strip()

    posted_at_raw = value(
        "posted_at",
        "",
    )

    posted_at = None

    if isinstance(
        posted_at_raw,
        datetime,
    ):
        posted_at = posted_at_raw

    elif posted_at_raw:

        try:
            posted_at = datetime.fromisoformat(
                str(posted_at_raw)
                .replace("Z", "+00:00")
            )

        except (
            TypeError,
            ValueError,
        ):
            posted_at = None

    skills_raw = value(
        "skills",
        [],
    )

    if isinstance(
        skills_raw,
        str,
    ):
        skills = [
            skills_raw.strip()
        ] if skills_raw.strip() else []

    else:
        try:
            skills = [
                str(skill).strip()
                for skill in skills_raw
                if str(skill).strip()
            ]

        except TypeError:
            skills = []

    workplace_lower = workplace_type.lower()

    remote = None

    if workplace_lower in {
        "remote",
        "fully remote",
        "remote work",
    }:
        remote = True

    elif workplace_lower in {
        "onsite",
        "on-site",
        "office",
        "hybrid",
    }:
        remote = workplace_lower == "remote"

    return CanonicalJob(
        title=str(
            value("title")
        ).strip(),

        company=str(
            value("company")
        ).strip(),

        location=str(
            value("location")
        ).strip(),

        url=str(
            value("url")
        ).strip(),

        source=str(
            value("source", "unknown")
        ).strip(),

        description=str(
            value("description")
        ).strip(),

        external_id=(
            source_id
            or None
        ),

        employment_type=(
            employment_type
            or None
        ),

        remote=remote,

        posted_at=posted_at,

        skills=skills,
    )


def normalize_jobs(
    jobs,
) -> list[CanonicalJob]:
    """
    Normalize multiple jobs while skipping invalid records.
    """

    normalized = []

    for job in jobs or []:

        try:

            item = normalize_job(
                job
            )

            if (
                item.title
                and item.url
            ):
                normalized.append(
                    item
                )

        except Exception:

            continue

    return normalized