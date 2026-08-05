class ApplicationAssistant:


    def generate_cv_points(
        self,
        job,
        profile
    ):

        points = []


        text = (

            job.get(
                "title",
                ""
            )
            +
            " "
            +
            job.get(
                "description",
                ""
            )

        ).lower()



        skills = profile.get(
            "skills",
            []
        )


        for skill in skills:

            if skill.lower() in text:

                points.append(

                    f"Experience with {skill}"

                )



        if "security" in text or "cyber" in text:

            points.append(

                "Cybersecurity education with hands-on security projects"

            )


        if "cloud" in text:

            points.append(

                "Experience deploying and managing cloud environments"

            )


        if "linux" in text:

            points.append(

                "Linux administration and troubleshooting experience"

            )


        return points



    def generate_interview_questions(
        self,
        job
    ):

        title = job.get(
            "title",
            ""
        )


        return [

            f"Explain your experience related to {title}",

            "Describe a security problem you solved",

            "How do you troubleshoot a technical issue?",

            "Explain your experience with Linux and networking"

        ]