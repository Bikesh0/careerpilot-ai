import requests

from app.search.base import JobProvider
from app.models.job import Job


class RemoteJobProvider(JobProvider):

    def fetch_jobs(self):

        jobs = []

        url = "https://remotive.com/api/remote-jobs"

        try:

            response = requests.get(
                url,
                timeout=10
            )

            data = response.json()


            for item in data.get("jobs", []):

                title = item.get("title", "").lower()

                description = item.get(
                    "description",
                    ""
                )


                text = (
                    title +
                    " " +
                    description
                ).lower()


                # Only cybersecurity/cloud related jobs

                keywords = [
                    "security",
                    "soc",
                    "cyber",
                    "cloud",
                    "devops",
                    "linux"
                ]


                if not any(
                    key in text
                    for key in keywords
                ):
                    continue



                jobs.append(
                    Job(
                        item.get("title"),
                        item.get("company_name"),
                        "Remote",
                        item.get("url"),
                        description,
                        "Remotive"
                    )
                )



        except Exception as error:

            print(
                "Remote provider error:",
                error
            )


        return jobs