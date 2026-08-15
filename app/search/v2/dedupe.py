from collections import OrderedDict

from .job import CanonicalJob


def deduplicate_jobs(jobs: list[CanonicalJob]) -> list[CanonicalJob]:
    """
    Deduplicate jobs while preserving discovery order.

    A source-specific external ID is preferred. Otherwise the
    normalized title/company/URL combination is used.
    """

    unique = OrderedDict()

    for job in jobs:
        key = job.dedupe_key()

        if key not in unique:
            unique[key] = job

    return list(unique.values())
