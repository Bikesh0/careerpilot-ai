from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CanonicalJob:
    """Normalized job representation used by the V2 search pipeline."""

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
        return " ".join(self.title.casefold().split())

    def normalized_company(self) -> str:
        company = " ".join(self.company.casefold().split())

        for suffix in (" oyj", " oy"):
            if company.endswith(suffix):
                company = company[:-len(suffix)].rstrip()
                break

        return company

    def normalized_location(self) -> str:
        location = " ".join(self.location.casefold().split())

        # Treat common Finnish country suffixes as equivalent.
        for suffix in (
            ", finland",
            " finland",
        ):
            if location.endswith(suffix):
                location = location[:-len(suffix)].rstrip(" ,")
                break

        return location

    def dedupe_key(self) -> str:
        if self.external_id:
            return (
                f"{self.source.casefold().strip()}:"
                f"{self.external_id.casefold().strip()}"
            )

        return "|".join(
            [
                self.normalized_title(),
                self.normalized_company(),
                self.normalized_location(),
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
            "posted_at": self.posted_at.isoformat()
            if self.posted_at
            else None,
            "skills": self.skills,
            "tags": self.tags,
            "discovered_at": self.discovered_at.isoformat(),
        }