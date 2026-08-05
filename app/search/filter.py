class JobFilter:


    ALLOWED_KEYWORDS = [

        # Cybersecurity
        "security",
        "cyber",
        "soc",
        "siem",
        "splunk",
        "incident",
        "threat",
        "vulnerability",
        "penetration",
        "iam",
        "identity",
        "access",

        # Cloud / DevOps security path
        "cloud",
        "aws",
        "azure",
        "docker",
        "kubernetes",
        "devops",
        "ci/cd",

        # Infrastructure path
        "linux",
        "system administrator",
        "systems administrator",
        "infrastructure",
        "network",
        "firewall",
        "server",

        # IT support path
        "it support",
        "technical support",
        "helpdesk",
        "service desk"

    ]


    BLOCKED_KEYWORDS = [

        "marketing",
        "sales",
        "finance",
        "accounting",
        "hr",
        "human resources",
        "recruiter",
        "designer",
        "graphic design",
        "social media"

    ]



    def get_text(self, job):

        if isinstance(job, dict):

            return (

                job.get("title", "")
                +
                " "
                +
                job.get("description", "")

            ).lower()


        return (

            job.title
            +
            " "
            +
            job.description

        ).lower()



    def remove_duplicates(
        self,
        jobs
    ):

        unique = []

        seen = set()


        for job in jobs:


            if isinstance(job, dict):

                title = job.get(
                    "title",
                    ""
                )

            else:

                title = job.title



            key = title.lower()



            if key not in seen:

                seen.add(key)

                unique.append(job)



        return unique




    def cybersecurity_only(
        self,
        jobs
    ):

        filtered = []



        for job in jobs:


            text = self.get_text(job)



            # Remove unrelated jobs

            if any(

                bad in text

                for bad in self.BLOCKED_KEYWORDS

            ):

                continue



            # Keep IT/security related jobs

            if any(

                good in text

                for good in self.ALLOWED_KEYWORDS

            ):

                filtered.append(job)



        return filtered