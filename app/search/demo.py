from app.search.job_model import Job


class DemoSearcher:


    def search(self):

        jobs = [

            Job(
                title="Security Engineer",
                company="Cyber Nordic",
                location="Helsinki Finland",
                description="""
                Security Engineer role.
                Requirements:
                Linux, Networking, Python,
                Firewall, IDS, IPS,
                Cyber Security.
                """,
                source="Demo"
            ),


            Job(
                title="Junior SOC Analyst",
                company="Security Finland",
                location="Helsinki Finland",
                description="""
                Junior SOC Analyst position.
                Responsibilities:
                Monitor SIEM alerts,
                investigate incidents,
                use Splunk,
                Linux and networking.
                """,
                source="Demo"
            ),


            Job(
                title="Cloud Support Engineer",
                company="Cloud Nordic",
                location="Helsinki Finland",
                description="""
                Cloud Support Engineer role.
                Skills:
                Linux, Cloud,
                Docker, Kubernetes,
                Python and troubleshooting.
                """,
                source="Demo"
            )

        ]


        print(
            "DemoSearcher found",
            len(jobs),
            "jobs"
        )


        return jobs