from dataclasses import dataclass

from app.search.v2.dedupe import deduplicate_jobs
from app.search.v2.job import CanonicalJob
from app.search.v2.normalizer import normalize_job
from app.search.v2.registry import create_sources


@dataclass
class SourceRunResult:
    source: str
    jobs: list[CanonicalJob]
    error: str = ""


class SourceRunner:
    """Execute job sources and return normalized, deduplicated jobs."""

    def __init__(self, sources=None):
        self.sources = (
            list(sources)
            if sources is not None
            else create_sources()
        )

    @staticmethod
    def _source_name(source) -> str:
        return getattr(
            source,
            "SOURCE",
            source.__class__.__name__,
        )

    def run_source(self, source) -> SourceRunResult:
        source_name = self._source_name(source)

        try:
            raw_jobs = source.search() or []
        except Exception as error:
            return SourceRunResult(
                source=source_name,
                jobs=[],
                error=str(error),
            )

        jobs = []

        for raw_job in raw_jobs:
            try:
                job = normalize_job(raw_job)

                if job.title and job.url:
                    jobs.append(job)

            except Exception as error:
                print(
                    f"[{source_name}] "
                    f"normalization failed: {error}"
                )

        print(
            f"[{source_name}] "
            f"normalized {len(jobs)} jobs"
        )

        return SourceRunResult(
            source=source_name,
            jobs=jobs,
        )

    def run(self) -> list[CanonicalJob]:
        all_jobs = []

        for source in self.sources:
            result = self.run_source(source)

            if result.error:
                print(
                    f"[{result.source}] "
                    f"source failed: {result.error}"
                )
                continue

            all_jobs.extend(result.jobs)

        unique_jobs = deduplicate_jobs(all_jobs)

        print(
            f"V2 collected "
            f"{len(unique_jobs)} unique jobs"
        )

        return unique_jobs