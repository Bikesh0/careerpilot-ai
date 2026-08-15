from .job import CanonicalJob


def normalize_job(raw) -> CanonicalJob:
    """
    Convert the existing V1 Job model or a compatible object
    into the V2 canonical job representation.
    """

    def value(name, default=""):
        result = getattr(raw, name, default)

        if result is None:
            return default

        return result

    return CanonicalJob(
        title=str(value("title")).strip(),
        company=str(value("company")).strip(),
        location=str(value("location")).strip(),
        url=str(value("url")).strip(),
        source=str(value("source", "unknown")).strip(),
        description=str(value("description")).strip(),
    )


def normalize_jobs(jobs) -> list[CanonicalJob]:
    normalized = []

    for job in jobs or []:
        try:
            item = normalize_job(job)

            if item.title and item.url:
                normalized.append(item)

        except Exception:
            continue

    return normalized
