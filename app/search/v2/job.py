from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CanonicalJob:
    title: str
    company: str
    location: str
    url: str
    source: str

    description: str = ""

    external_id: Optional[str] = None
    employment_type: Optional[str] = None
    remote: Optional[bool] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    posted_at: Optional[datetime] = None

    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    discovered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def normalized_title(self) -> str:
        return " ".join(self.title.lower().split())

    def normalized_company(self) -> str:
        return " ".join(self.company.lower().split())

    def dedupe_key(self) -> str:
        if self.external_id:
            return f"{self.source}:{self.external_id}".lower()

        return "|".join(
            [
                self.normalized_title(),
                self.normalized_company(),
                self.url.rstrip("/").lower(),
            ]
        )

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "description": self.description,
            "external_id": self.external_id,
            "employment_type": self.employment_type,
            "remote": self.remote,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "posted_at": (
                self.posted_at.isoformat()
                if self.posted_at
                else None
            ),
            "skills": self.skills,
            "tags": self.tags,
            "discovered_at": self.discovered_at.isoformat(),
        }
