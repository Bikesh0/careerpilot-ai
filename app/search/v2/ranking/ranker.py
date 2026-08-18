from dataclasses import dataclass
from typing import Iterable

from app.search.v2.job import CanonicalJob
from app.search.v2.matching import JobMatcher
from app.search.v2.matching.result import MatchResult


@dataclass
class RankedJob:
    """A canonical job together with its match result."""

    job: CanonicalJob
    match: MatchResult
    rank: int = 0

    @property
    def score(self) -> float:
        return self.match.score

    def to_dict(self) -> dict:
        data = self.job.to_dict()
        data["rank"] = self.rank
        data["score"] = self.match.score
        data["match"] = self.match.to_dict()
        return data


class JobRanker:
    """Score and rank canonical jobs against a search profile."""

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

    def score(self, job: CanonicalJob) -> RankedJob:
        match = self.matcher.score_job(job)
        return RankedJob(job=job, match=match)

    def rank(
        self,
        jobs: Iterable[CanonicalJob],
        limit: int = None,
    ) -> list[RankedJob]:
        if limit is not None and limit <= 0:
            return []

        ranked = [self.score(job) for job in jobs or []]

        ranked.sort(key=self._sort_key, reverse=True)

        for index, item in enumerate(ranked, start=1):
            item.rank = index

        return ranked[:limit] if limit is not None else ranked

    @staticmethod
    def _sort_key(item: RankedJob):
        job = item.job

        posted_at = job.posted_at
        posted_timestamp = (
            posted_at.timestamp() if posted_at is not None else 0.0
        )

        return (
            item.match.score,
            item.match.title_score,
            item.match.skill_score,
            item.match.location_score,
            posted_timestamp,
        )
