
from typing import Iterable

from app.search.v2.matching.result import MatchResult
from app.search.v2.matching.signals import (
    find_skill_matches,
    title_matches,
)


class JobMatcher:

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
        "intern": [
            "intern",
            "internship",
            "trainee",
        ],
        "junior": [
            "junior",
            "jr",
        ],
        "entry": [
            "entry level",
            "entry-level",
            "graduate",
        ],
        "mid": [
            "mid",
            "mid-level",
            "mid level",
        ],
        "senior": [
            "senior",
            "sr",
        ],
        "lead": [
            "lead",
            "team lead",
            "tech lead",
            "technical lead",
        ],
        "manager": [
            "manager",
            "management",
        ],
        "director": [
            "director",
        ],
        "architect": [
            "architect",
        ],
    }

    def __init__(
        self,
        profile_skills: Iterable[str] = None,
        target_titles: Iterable[str] = None,
        target_locations: Iterable[str] = None,
    ):
        self.profile_skills = list(
            profile_skills or []
        )

        self.target_titles = list(
            target_titles or []
        )

        self.target_locations = list(
            target_locations or []
        )

    def score_job(self, job) -> MatchResult:

        # -----------------------------------------------------
        # Skills
        # -----------------------------------------------------

        matched_skills, missing_skills = find_skill_matches(
            job,
            self.profile_skills,
        )

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        matched_titles = title_matches(
            job,
            self.target_titles,
        )

        title_score = (
            100.0
            if matched_titles
            else 0.0
        )

        # -----------------------------------------------------
        # Skill score
        # -----------------------------------------------------

        if self.profile_skills:

            skill_score = (
                len(matched_skills)
                / len(self.profile_skills)
                * 100.0
            )

        else:

            skill_score = 0.0

        # -----------------------------------------------------
        # Location
        # -----------------------------------------------------

        location = str(
            getattr(
                job,
                "location",
                "",
            )
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

        # -----------------------------------------------------
        # Seniority
        # -----------------------------------------------------

        seniority, seniority_score = (
            self._detect_seniority(job)
        )

        if seniority == "unspecified":
            seniority_score = (
                self.SENIORITY_SCORES[
                    "unspecified"
                ]
            )

        # -----------------------------------------------------
        # Final score
        # -----------------------------------------------------

        score = (
            title_score * 0.40
            + skill_score * 0.35
            + location_score * 0.15
            + seniority_score * 0.10
        )

        # -----------------------------------------------------
        # Reasons
        # -----------------------------------------------------

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

        if seniority != "unspecified":

            if seniority in {
                "intern",
                "junior",
                "entry",
            }:

                reasons.append(
                    f"{seniority} seniority is a good fit"
                )

            elif seniority == "mid":

                reasons.append(
                    "mid-level seniority is a moderate fit"
                )

            elif seniority in {
                "senior",
                "lead",
                "manager",
                "architect",
                "director",
            }:

                reasons.append(
                    f"{seniority} seniority reduces the match"
                )

        if missing_skills:

            reasons.append(
                f"{len(missing_skills)} profile skills not found"
            )

        # -----------------------------------------------------
        # Job ID
        # -----------------------------------------------------

        job_id = str(
            getattr(
                job,
                "external_id",
                None,
            )
            or getattr(
                job,
                "url",
                "",
            )
            or getattr(
                job,
                "title",
                "",
            )
        )

        # -----------------------------------------------------
        # Result
        # -----------------------------------------------------

        return MatchResult(
            job_id=job_id,
            score=round(
                max(
                    min(score, 100.0),
                    0.0,
                ),
                2,
            ),
            reasons=reasons,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            title_score=round(
                title_score,
                2,
            ),
            skill_score=round(
                skill_score,
                2,
            ),
            location_score=round(
                location_score,
                2,
            ),
            seniority_score=round(
                seniority_score,
                2,
            ),
        )

    # =========================================================
    # Seniority detection
    # =========================================================

    def _detect_seniority(
        self,
        job,
    ):
        """
        Detect seniority primarily from the job title.

        Title signals are deliberately stronger than description
        signals because descriptions often mention multiple levels.
        """

        title = str(
            getattr(
                job,
                "title",
                "",
            )
            or ""
        ).lower()

        description = str(
            getattr(
                job,
                "description",
                "",
            )
            or ""
        ).lower()

        ordered_levels = [
            "director",
            "manager",
            "architect",
            "lead",
            "senior",
            "mid",
            "junior",
            "entry",
            "intern",
        ]

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        for level in ordered_levels:

            for term in self.SENIORITY_TERMS[level]:

                if self._term_in_text(
                    term,
                    title,
                ):

                    return (
                        level,
                        self.SENIORITY_SCORES[level],
                    )

        # -----------------------------------------------------
        # Description
        # -----------------------------------------------------

        for level in ordered_levels:

            for term in self.SENIORITY_TERMS[level]:

                if self._term_in_text(
                    term,
                    description,
                ):

                    return (
                        level,
                        self.SENIORITY_SCORES[level] * 0.5,
                    )

        # -----------------------------------------------------
        # No seniority signal
        # -----------------------------------------------------

        return (
            "unspecified",
            self.SENIORITY_SCORES[
                "unspecified"
            ],
        )

    # =========================================================
    # Term matching
    # =========================================================

    def _term_in_text(
        self,
        term,
        text,
    ):
        term = str(
            term or ""
        ).strip().lower()

        text = str(
            text or ""
        ).strip().lower()

        if not term or not text:
            return False

        if " " in term:

            return term in text

        words = (
            text
            .replace(
                "/",
                " ",
            )
            .replace(
                "-",
                " ",
            )
            .split()
        )

        return term in words
