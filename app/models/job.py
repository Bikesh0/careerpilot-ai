class Job:
    def __init__(
        self,
        title="",
        company="",
        location="",
        url="",
        description="",
        source="",
        source_id="",
        posted_at="",
        employment_type="",
        workplace_type="",
        salary="",
        skills=None,
    ):
        self.id = None

        # Basic job information
        self.title = title or ""
        self.company = company or ""
        self.location = location or ""
        self.url = url or ""
        self.description = description or ""

        # Source information
        self.source = source or ""
        self.source_id = source_id or ""

        # Additional job information
        self.posted_at = posted_at or ""
        self.employment_type = employment_type or ""
        self.workplace_type = workplace_type or ""
        self.salary = salary or ""

        # Skills extracted/provided by the job source
        self.skills = skills if skills is not None else []

        # Matching information
        self.match_score = 0
        self.matched_skills = []

    def __repr__(self):
        return (
            f"Job("
            f"title={self.title!r}, "
            f"company={self.company!r}, "
            f"location={self.location!r}, "
            f"source={self.source!r}"
            f")"
        )