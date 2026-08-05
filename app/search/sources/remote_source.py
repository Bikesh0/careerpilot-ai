import requests

from app.models.job import Job


class RemoteJobSource:

    URL = "https://remotive.com/api/remote-jobs"

    KEYWORDS = [
        "security",
        "cyber",
        "soc",
        "cloud",
        "devops",
        "linux",
        "network",
        "infrastructure",
        "azure",
        "aws",
        "kubernetes",
        "docker",
        "iam",
        "identity",
        "firewall",
        "splunk",
        "siem"
    ]

    def search(self):

        jobs = []

        try:

            response = requests.get(
                self.URL,
                timeout=15
            )

            response.raise_for_status()

            data = response.json()

            for item in data.get("jobs", []):

                title = item.get("title", "")

                description = item.get(
                    "description",
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

                jobs.append(
                    Job(
                        title=title,
                        company=item.get(
                            "company_name",
                            ""
                        ),
                        location="Remote",
                        url=item.get(
                            "url",
                            ""
                        ),
                        description=description,
                        source="Remotive"
                    )
                )

        except Exception as error:

            print(
                "Remote source error:",
                error
            )

        return jobs