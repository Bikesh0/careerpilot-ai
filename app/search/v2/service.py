from typing import Iterable, List

from app.search.v2.runner import SourceRunner
from app.search.v2.ranking import JobRanker, RankedJob


class V2SearchService:

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

    def search(
        self,
        limit: int = 50,
    ) -> List[RankedJob]:

        jobs = self.runner.run()

        return self.ranker.rank(
            jobs,
            limit=limit,
        )
