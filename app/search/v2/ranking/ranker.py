from typing import Iterable, List

from app.search.v2.matching import JobMatcher
from app.search.v2.matching.result import MatchResult


class RankedJob:
    def __init__(self, job, match: MatchResult):
        self.job = job
        self.match = match

    @property
    def score(self):
        return self.match.score

    def to_dict(self):
        data = self.job.to_dict()
        data["match"] = self.match.to_dict()
        return data


class JobRanker:

    def __init__(
        self,
        profile_skills: Iterable[str] = None,
        target_titles: Iterable[str] = None,
        target_locations: Iterable[str] = None,
    ):
        self.matcher = JobMatcher(
            profile_skills=profile_skills,
            target_titles=target_titles,
            target_locations=target_locations,
        )

    def rank(
        self,
        jobs: Iterable,
        limit: int = None,
    ) -> List[RankedJob]:

        ranked = []

        for job in jobs or []:
            match = self.matcher.score_job(job)

            ranked.append(
                RankedJob(
                    job=job,
                    match=match,
                )
            )

        ranked.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        if limit is not None:
            return ranked[:limit]

        return ranked
