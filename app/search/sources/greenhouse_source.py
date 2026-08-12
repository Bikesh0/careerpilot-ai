import requests

from app.models.job import Job


class GreenhouseSource:

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    # Real company board tokens.
    # We will expand this list as we verify more Finnish companies.
    BOARDS = {
        "aiven": "Aiven"
    }

    KEYWORDS = [
        "security",
        "cyber",
        "soc",
        "siem",
        "network",
        "linux",
        "cloud",
        "devops",
        "infrastructure",
        "iam",
        "identity",
        "firewall",
        "incident response",
        "information security",
        "python",
        "kubernetes",
        "docker"
    ]

    def search(self):

        jobs = []

        for board_token, company_name in self.BOARDS.items():

            url = (
                f"{self.BASE_URL}/"
                f"{board_token}/jobs"
                f"?content=true"
            )

            try:

                response = requests.get(
                    url,
                    timeout=20
                )

                response.raise_for_status()

                data = response.json()

                for item in data.get("jobs", []):

                    title = item.get(
                        "title",
                        ""
                    )

                    description = item.get(
                        "content",
                        ""
                    )

                    location_data = item.get(
                        "location",
                        {}
                    )

                    location = location_data.get(
                        "name",
                        ""
                    )

                    text = (
                        title +
                        " " +
                        description
                    ).lower()

                    if not any(
                        keyword in text
                        for keyword in self.KEYWORDS
                    ):
                        continue

                    job_url = item.get(
                        "absolute_url",
                        ""
                    )

                    jobs.append(
                        Job(
                            title=title,
                            company=company_name,
                            location=location,
                            url=job_url,
                            description=description,
                            source="Greenhouse",
                            source_url=job_url,
                            company_url=(
                                f"https://{board_token}.com"
                            ),
                            published_at=item.get(
                                "first_published"
                            )
                        )
                    )

            except Exception as error:

                print(
                    f"Greenhouse source error "
                    f"({company_name}):",
                    error
                )

        return jobs