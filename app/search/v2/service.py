from typing import Iterable

from app.search.v2.ranking import JobRanker, RankedJob
from app.search.v2.runner import SourceRunner


class V2SearchService:
    """Application-facing V2 search service."""

    def __init__(
        self,
        sources=None,
        profile_skills: Iterable[str] = None,
        target_titles: Iterable[str] = None,
        target_locations: Iterable[str] = None,
    ):
        self.runner = SourceRunner(sources=sources)

        self.ranker = JobRanker(
            profile_skills=profile_skills,
            target_titles=target_titles,
            target_locations=target_locations,
        )

    def search(self, limit: int = 50) -> list[RankedJob]:
        jobs = self.runner.run()
        return self.ranker.rank(jobs, limit=limit)

    def search_jobs(self, limit: int = 50) -> list[dict]:
        return [
            item.to_dict()
            for item in self.search(limit=limit)
        ]