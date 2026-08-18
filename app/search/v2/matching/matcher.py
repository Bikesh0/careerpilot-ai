from typing import Iterable

from app.search.v2.matching.result import MatchResult
from app.search.v2.matching.signals import (
    extract_required_experience_years,
    extract_text,
    find_skill_matches,
    location_matches,
    title_matches,
)


class JobMatcher:
    """Score a canonical job against a user's search profile."""

    SENIORITY_SCORES = {
        "intern": 100.0,
        "junior": 90.0,
        "entry": 90.0,
        "unspecified": 70.0,
        "mid": 60.0,
        "senior": 35.0,
        "lead": 20.0,
        "manager": 10.0,
        "architect": 10.0,
        "director": 5.0,
    }

    SENIORITY_TERMS = {
        "intern": ["intern", "internship", "trainee"],
        "junior": ["junior", "jr"],
        "entry": ["entry level", "entry-level", "graduate"],
        "mid": ["mid", "mid-level", "mid level"],
        "senior": ["senior", "sr"],
        "lead": ["lead", "team lead", "tech lead", "technical lead"],
        "manager": ["manager", "management"],
        "director": ["director"],
        "architect": ["architect"],
    }

    # Ported from app.ai.matcher.JobMatcher.EXCLUDED_TITLE_TERMS. This
    # is generic (not profile-specific), so it belongs in code rather
    # than profiles/profile.json - unlike target_titles, which is
    # candidate-specific data.
    EXCLUDED_TITLE_TERMS = [
        "marketing",
        "sales",
        "account executive",
        "business development",
        "business developer",
        "recruiter",
        "recruitment",
        "talent acquisition",
        "human resources",
        "hr manager",
        "designer",
        "graphic designer",
        "ux designer",
        "ui designer",
        "content writer",
        "copywriter",
        "teacher",
        "accountant",
        "finance manager",
        "financial analyst",
        "legal counsel",
        "lawyer",
        "product marketing",
        "communications manager",
        "head of marketing",
        "social media manager",
        "customer success manager",
        "sales manager",
        "sales representative",
    ]

    # Ported from app.ai.matcher.JobMatcher._experience_requirement_penalty
    # - same thresholds, verified against real postings in that matcher.
    # A posting requiring more experience than a junior/entry-level
    # candidate realistically has is penalized on a sliding scale.
    EXPERIENCE_REQUIREMENT_PENALTIES = (
        (7, 20.0),
        (5, 15.0),
        (4, 11.0),
        (3, 7.0),
        (2, 3.0),
    )

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
        job_id = str(
            getattr(job, "external_id", None)
            or getattr(job, "url", "")
            or getattr(job, "title", "")
        )

        title = str(getattr(job, "title", "") or "")

        if self._title_is_excluded(title):
            return MatchResult(
                job_id=job_id,
                score=0.0,
                reasons=[
                    "Excluded: title matches an unrelated role "
                    "(e.g. marketing, sales, HR)"
                ],
                excluded=True,
            )

        matched_skills, missing_skills = find_skill_matches(
            job, self.profile_skills
        )
        matched_titles = title_matches(job, self.target_titles)
        matched_locations = location_matches(job, self.target_locations)

        title_score = 100.0 if matched_titles else 0.0
        skill_score = (
            len(matched_skills) / len(self.profile_skills) * 100.0
            if self.profile_skills else 0.0
        )
        location_score = 100.0 if matched_locations else 0.0

        seniority, seniority_score = self._detect_seniority(job)

        score = (
            title_score * 0.40
            + skill_score * 0.35
            + location_score * 0.15
            + seniority_score * 0.10
        )

        reasons = []
        if matched_titles:
            reasons.append("Target job title matched")
        if matched_skills:
            reasons.append(f"Matched {len(matched_skills)} profile skills")
        if matched_locations:
            reasons.append("Target location matched")

        if seniority != "unspecified":
            if seniority in {"intern", "junior", "entry"}:
                reasons.append(f"{seniority} seniority is a good fit")
            elif seniority == "mid":
                reasons.append("mid-level seniority is a moderate fit")
            else:
                reasons.append(f"{seniority} seniority reduces the match")

        if missing_skills:
            reasons.append(f"{len(missing_skills)} profile skills not found")

        required_years = extract_required_experience_years(
            extract_text(job)
        )
        experience_penalty = self._experience_requirement_penalty(
            required_years
        )

        if experience_penalty:
            score -= experience_penalty
            reasons.append(
                f"Requires {required_years}+ years experience"
            )

        return MatchResult(
            job_id=job_id,
            score=round(max(min(score, 100.0), 0.0), 2),
            reasons=reasons,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            title_score=round(title_score, 2),
            skill_score=round(skill_score, 2),
            location_score=round(location_score, 2),
            seniority_score=round(seniority_score, 2),
        )

    def _title_is_excluded(self, title):
        for term in self.EXCLUDED_TITLE_TERMS:
            if self._term_in_text(term, title):
                return True
        return False

    @classmethod
    def _experience_requirement_penalty(cls, years):
        if years is None:
            return 0.0

        for threshold, penalty in cls.EXPERIENCE_REQUIREMENT_PENALTIES:
            if years >= threshold:
                return penalty

        return 0.0

    def _detect_seniority(self, job):
        title = str(getattr(job, "title", "") or "").lower()
        description = str(getattr(job, "description", "") or "").lower()

        ordered_levels = [
            "director", "manager", "architect", "lead", "senior",
            "mid", "junior", "entry", "intern",
        ]

        for level in ordered_levels:
            for term in self.SENIORITY_TERMS[level]:
                if self._term_in_text(term, title):
                    return level, self.SENIORITY_SCORES[level]

        for level in ordered_levels:
            for term in self.SENIORITY_TERMS[level]:
                if self._term_in_text(term, description):
                    return level, self.SENIORITY_SCORES[level] * 0.5

        return "unspecified", self.SENIORITY_SCORES["unspecified"]

    @staticmethod
    def _term_in_text(term, text):
        from app.search.v2.matching.signals import _contains_term
        return _contains_term(text, term)
