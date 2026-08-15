from dataclasses import dataclass
from typing import List

from app.search.v2.dedupe import deduplicate_jobs
from app.search.v2.normalizer import normalize_job
from app.search.v2.registry import create_sources
from app.search.v2.job import CanonicalJob


@dataclass
class SourceRunResult:
    source: str
    jobs: List[CanonicalJob]
    error: str = ""


class SourceRunner:

    def __init__(self, sources=None):
        self.sources = sources if sources is not None else create_sources()

    def run_source(self, source) -> SourceRunResult:
        source_name = getattr(
            source,
            "SOURCE",
            source.__class__.__name__,
        )

        try:
            raw_jobs = source.search() or []

            jobs = []

            for raw_job in raw_jobs:
                try:
                    jobs.append(normalize_job(raw_job))
                except Exception as error:
                    print(
                        f"[{source_name}] "
                        f"normalization failed: {error}"
                    )

            return SourceRunResult(
                source=source_name,
                jobs=jobs,
            )

        except Exception as error:
            return SourceRunResult(
                source=source_name,
                jobs=[],
                error=str(error),
            )

    def run(self) -> List[CanonicalJob]:
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

        return deduplicate_jobs(all_jobs)
