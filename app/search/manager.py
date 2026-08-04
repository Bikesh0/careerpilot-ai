from app.models.job import Job


class SearchManager:

    def search_jobs(self):

        return [
            Job(
                "Junior SOC Analyst",
                "Security Finland",
                "Helsinki",
                "https://example.com",
                "Monitor SIEM alerts, investigate security incidents, Linux networking",
                "Demo"
            ),

            Job(
                "Cloud Support Engineer",
                "Cloud Nordic",
                "Espoo",
                "https://example.com",
                "Linux servers, cloud infrastructure, Docker and troubleshooting",
                "Demo"
            ),

            Job(
                "Frontend Developer",
                "Web Company",
                "Helsinki",
                "https://example.com",
                "React Javascript UI development",
                "Demo"
            )
        ]