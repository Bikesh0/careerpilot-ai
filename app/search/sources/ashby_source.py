import requests

from app.models.job import Job


class AshbySource:

    API_URL = "https://api.ashbyhq.com/posting-api/job-board"

    BOARDS = {
        "hoxhunt": "Hoxhunt",
        "Reaktor": "Reaktor",
        "mapbox": "Mapbox",
    }

    FINLAND_KEYWORDS = [
        "finland",
        "helsinki",
        "espoo",
        "vantaa",
        "turku",
        "tampere",
        "oulu",
        "fin",
    ]

    RELEVANT_KEYWORDS = [
        "security",
        "cybersecurity",
        "cyber security",
        "soc",
        "siem",
        "security operations",
        "information security",
        "infosec",
        "iam",
        "identity",
        "incident response",
        "threat",
        "network",
        "network security",
        "cloud",
        "cloud security",
        "linux",
        "devops",
        "infrastructure",
        "system administrator",
        "systems administrator",
        "technical support",
        "support engineer",
        "it support",
        "helpdesk",
        "service desk",
        "python",
        "kubernetes",
        "docker",
    ]

    def search(self):

        jobs = []

        for board_token, company_name in self.BOARDS.items():

            url = f"{self.API_URL}/{board_token}"

            try:

                response = requests.get(
                    url,
                    timeout=20
                )

                response.raise_for_status()

                data = response.json()

                postings = data.get(
                    "jobs",
                    data.get("postings", [])
                )

                print(
                    f"Ashby {company_name}: "
                    f"{len(postings)} postings received"
                )

                for item in postings:

                    title = (
                        item.get("title", "")
                        or ""
                    ).strip()

                    description = (
                        item.get("description", "")
                        or ""
                    ).strip()

                    location = (
                        item.get("location", "")
                        or ""
                    )

                    if isinstance(location, dict):
                        location = (
                            location.get("name", "")
                            or ""
                        )

                    location = str(location).strip()

                    job_url = (
                        item.get("jobUrl")
                        or item.get("job_url")
                        or item.get("url")
                        or ""
                    )

                    source_id = (
                        item.get("id")
                        or item.get("jobId")
                        or ""
                    )

                    posted_at = (
                        item.get("publishedAt")
                        or item.get("published_at")
                        or ""
                    )

                    text = (
                        title
                        + " "
                        + description
                        + " "
                        + location
                    ).lower()

                    # Keep only jobs relevant to the
                    # user's technical/security profile.
                    if not self.is_relevant(text):
                        continue

                    # Finland is the main target.
                    # Remote jobs remain allowed.
                    if not self.is_finland_or_remote(text):
                        continue

                    jobs.append(
                        Job(
                            title=title,
                            company=company_name,
                            location=location,
                            url=job_url,
                            description=description,
                            source="Ashby",
                            source_id=source_id,
                            posted_at=posted_at,
                        )
                    )

            except Exception as error:

                print(
                    f"Ashby source error "
                    f"({company_name}):",
                    error
                )

        return jobs

    def is_relevant(self, text):

        return any(
            keyword in text
            for keyword in self.RELEVANT_KEYWORDS
        )

    def is_finland_or_remote(self, text):

        if any(
            keyword in text
            for keyword in self.FINLAND_KEYWORDS
        ):
            return True

        remote_keywords = [
            "remote",
            "hybrid",
            "work from anywhere",
            "remote-friendly",
        ]

        return any(
            keyword in text
            for keyword in remote_keywords
        )