import requests

from app.models.job import Job
from app.search.search_profile import SearchProfile


class RemoteJobSource:

    URL = "https://remotive.com/api/remote-jobs"

    def __init__(self):
        self.profile = SearchProfile()

    def search(self):

        jobs = []

        try:
            response = requests.get(
                self.URL,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

            for item in data.get("jobs", []):

                title = item.get("title", "").strip()
                description = item.get("description", "").strip()
                company = item.get("company_name", "").strip()

                location = item.get(
                    "candidate_required_location",
                    "Remote"
                )

                if not location:
                    location = "Remote"

                if not title or not company:
                    continue

                if not self.is_relevant(title, description):
                    continue

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        location=location,
                        url=item.get("url", "").strip(),
                        description=description,
                        source="Remotive",
                        source_id=str(item.get("id", "")),
                        posted_at=item.get(
                            "publication_date",
                            ""
                        ),
                        employment_type=item.get(
                            "job_type",
                            ""
                        ),
                        workplace_type="Remote"
                    )
                )

        except requests.RequestException as error:

            print(
                "Remotive network error:",
                error
            )

        except Exception as error:

            print(
                "Remotive source error:",
                error
            )

        return jobs

    def is_relevant(self, title, description):

        title_text = title.lower()
        description_text = description.lower()

        full_text = (
            title_text +
            " " +
            description_text
        )

        # ---------------------------------------------
        # Relevant job titles
        # ---------------------------------------------

        relevant_titles = [
            "soc analyst",
            "soc analyst tier 1",
            "soc analyst tier 2",
            "cybersecurity analyst",
            "cyber security analyst",
            "security analyst",
            "information security analyst",
            "information security",
            "cybersecurity",
            "cyber security",
            "security engineer",
            "security specialist",
            "information security specialist",
            "security operations",
            "security operations analyst",
            "iam analyst",
            "iam engineer",
            "identity and access",
            "identity access management",
            "cloud security",
            "cloud security engineer",
            "network security",
            "network security engineer",
            "security administrator",
            "it security",
            "it security specialist",
            "security consultant",
            "junior security",
            "security trainee",
            "cybersecurity trainee",
            "security intern",
            "cybersecurity intern",
            "devsecops",
            "security operations center"
        ]

        for target in relevant_titles:

            if target in title_text:
                return True

        # ---------------------------------------------
        # Related technical titles
        # ---------------------------------------------

        related_titles = [
            "system administrator",
            "systems administrator",
            "linux administrator",
            "linux engineer",
            "network administrator",
            "network engineer",
            "cloud engineer",
            "cloud support",
            "devops engineer",
            "site reliability engineer",
            "infrastructure engineer",
            "technical support",
            "it support",
            "help desk",
            "service desk"
        ]

        related_skill_words = [
            "linux",
            "networking",
            "tcp/ip",
            "firewall",
            "vpn",
            "siem",
            "splunk",
            "ids",
            "ips",
            "kubernetes",
            "docker",
            "aws",
            "azure",
            "google cloud",
            "gcp",
            "iam",
            "identity",
            "active directory",
            "vmware",
            "penetration testing",
            "vulnerability",
            "incident response"
        ]

        related_title_match = any(
            target in title_text
            for target in related_titles
        )

        matched_skills = sum(
            1
            for skill in related_skill_words
            if skill in full_text
        )

        # A related IT/cloud/network job needs
        # multiple relevant technical signals.
        if related_title_match and matched_skills >= 2:
            return True

        # ---------------------------------------------
        # Strong cybersecurity signal anywhere
        # ---------------------------------------------

        security_words = [
            "soc",
            "cybersecurity",
            "cyber security",
            "information security",
            "infosec",
            "security operations",
            "iam",
            "identity and access management"
        ]

        security_match = any(
            word in full_text
            for word in security_words
        )

        if security_match and matched_skills >= 1:
            return True

        return False