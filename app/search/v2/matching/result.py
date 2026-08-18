from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MatchResult:
    job_id: str
    score: float
    reasons: List[str] = field(default_factory=list)
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    title_score: float = 0.0
    skill_score: float = 0.0
    location_score: float = 0.0
    seniority_score: float = 0.0
    excluded: bool = False

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "score": self.score,
            "reasons": self.reasons,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "title_score": self.title_score,
            "skill_score": self.skill_score,
            "location_score": self.location_score,
            "seniority_score": self.seniority_score,
            "excluded": self.excluded,
        }
