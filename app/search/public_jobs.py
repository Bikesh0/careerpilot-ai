from app.search.base import JobProvider
from app.models.job import Job


class PublicJobProvider(JobProvider):


    def fetch_jobs(self):

        jobs = []


        # Placeholder for API connection
        # Next step we connect real APIs here


        jobs.append(
            Job(
                "SOC Analyst",
                "Example Security Company",
                "Helsinki",
                "https://example.com",
                "SIEM Splunk Linux incident response cybersecurity",
                "Public API"
            )
        )


        jobs.append(
            Job(
                "Cloud Security Engineer",
                "Example Cloud Company",
                "Espoo",
                "https://example.com",
                "AWS Azure Docker Kubernetes security monitoring",
                "Public API"
            )
        )


        return jobs