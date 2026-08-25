from collections.abc import Iterable

from .job import CanonicalJob


def deduplicate_jobs(
    jobs: Iterable[CanonicalJob],
) -> list[CanonicalJob]:
    """
    Remove duplicate canonical jobs while preserving first-seen order.

    A job is treated as a duplicate of an earlier one if EITHER signal
    matches:
    - ``dedupe_key()`` - source+external_id when available, otherwise
      normalized title+company+location.
    - ``canonical_url()`` - the same posting reached through the same
      URL (tracking parameters stripped), the common case for the same
      job appearing on more than one aggregator/source.

    Either signal alone can under-catch real duplicates (two sources
    rarely share an external_id; a title/company/location match can
    miss a slightly reworded re-post) - checking both, independently,
    catches more of the real-world duplicate patterns V1's dedup
    already handled (app.search.manager.SearchManager) without
    requiring V2 to depend on V1's implementation.
    """

    seen_keys: set[str] = set()
    seen_urls: set[str] = set()
    unique: list[CanonicalJob] = []

    for job in jobs or []:
        if not isinstance(job, CanonicalJob):
            continue

        key = job.dedupe_key()
        url_key = job.canonical_url()

        if key in seen_keys:
            continue

        if url_key and url_key in seen_urls:
            continue

        seen_keys.add(key)

        if url_key:
            seen_urls.add(url_key)

        unique.append(job)

    return unique