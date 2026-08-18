from collections.abc import Iterable

from .job import CanonicalJob


def deduplicate_jobs(
    jobs: Iterable[CanonicalJob],
) -> list[CanonicalJob]:
    """Remove duplicate canonical jobs while preserving first-seen order."""

    seen: set[str] = set()
    unique: list[CanonicalJob] = []

    for job in jobs or []:
        if not isinstance(job, CanonicalJob):
            continue

        key = job.dedupe_key()

        if key in seen:
            continue

        seen.add(key)
        unique.append(job)

    return unique