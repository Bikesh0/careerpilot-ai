from dataclasses import dataclass

from .job import CanonicalJob


@dataclass
class SourceResult:
    source: str
    jobs: list[CanonicalJob]
    error: str | None = None

    @property
    def count(self) -> int:
        return len(self.jobs)


class IngestionPipeline:

    def __init__(self, sources):
        self.sources = list(sources)

    def run(self) -> list[SourceResult]:
        results = []

        for source in self.sources:
            source_name = getattr(
                source,
                "SOURCE",
                source.__class__.__name__,
            )

            try:
                raw_jobs = source.search() or []

                jobs = []

                for raw in raw_jobs:
                    try:
                        job = self._normalize(raw)

                        if job.title and job.url:
                            jobs.append(job)

                    except Exception:
                        continue

                results.append(
                    SourceResult(
                        source=source_name,
                        jobs=jobs,
                    )
                )

            except Exception as error:
                results.append(
                    SourceResult(
                        source=source_name,
                        jobs=[],
                        error=str(error),
                    )
                )

        return results

    @staticmethod
    def _normalize(raw) -> CanonicalJob:
        from .normalizer import normalize_job

        return normalize_job(raw)
