from typing import Iterable

from app.search.v2.matching.result import MatchResult
from app.search.v2.matching.signals import (
    find_skill_matches,
    title_matches,
)


class JobMatcher:

    def __init__(
        self,
        profile_skills: Iterable[str] = None,
        target_titles: Iterable[str] = None,
        target_locations: Iterable[str] = None,
    ):
        self.profile_skills = list(profile_skills or [])
        self.target_titles = list(target_titles or [])
        self.target_locations = list(target_locations or [])

    def score_job(self, job) -> MatchResult:

        matched_skills, missing_skills = find_skill_matches(
            job,
            self.profile_skills,
        )

        matched_titles = title_matches(
            job,
            self.target_titles,
        )

        title_score = 100.0 if matched_titles else 0.0

        if self.profile_skills:
            skill_score = (
                len(matched_skills)
                / len(self.profile_skills)
                * 100.0
            )
        else:
            skill_score = 0.0

        location = str(
            getattr(job, "location", "")
            or ""
        ).lower()

        location_matches = [
            target
            for target in self.target_locations
            if str(target).lower() in location
        ]

        location_score = (
            100.0
            if location_matches
            else 0.0
        )

        seniority_score = 0.0

        score = (
            title_score * 0.35
            + skill_score * 0.45
            + location_score * 0.20
        )

        reasons = []

        if matched_titles:
            reasons.append(
                "Target job title matched"
            )

        if matched_skills:
            reasons.append(
                f"Matched {len(matched_skills)} profile skills"
            )

        if location_matches:
            reasons.append(
                "Target location matched"
            )

        if missing_skills:
            reasons.append(
                f"{len(missing_skills)} profile skills not found"
            )

        job_id = str(
            getattr(job, "external_id", None)
            or getattr(job, "url", "")
            or getattr(job, "title", "")
        )

        return MatchResult(
            job_id=job_id,
            score=round(score, 2),
            reasons=reasons,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            title_score=round(title_score, 2),
            skill_score=round(skill_score, 2),
            location_score=round(location_score, 2),
            seniority_score=round(seniority_score, 2),
        )
