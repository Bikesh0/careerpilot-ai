class JobMatcher:


    def skill_score(self, job, profile):

        text = job.description.lower()

        matched = []

        for skill in profile["skills"]:

            if skill.lower() in text:
                matched.append(skill)


        score = 0

        if profile["skills"]:
            score = (
                len(matched)
                /
                len(profile["skills"])
            ) * 100


        return round(score), matched



    def role_score(self, job, profile):

        title = job.title.lower()

        for role in profile["target_roles"]:

            if role.lower() in title:
                return 100

        return 40



    def education_score(self, profile):

        if len(profile["education"]) > 0:
            return 100

        return 0



    def location_score(self, job, profile):

        if profile["location"].lower() in job.location.lower():
            return 100

        return 50



    def rank_jobs(self, jobs, profile):

        results = []


        for job in jobs:

            skills, matched = self.skill_score(
                job,
                profile
            )

            role = self.role_score(
                job,
                profile
            )

            education = self.education_score(
                profile
            )

            location = self.location_score(
                job,
                profile
            )


            final_score = round(

                skills * 0.40 +

                role * 0.25 +

                education * 0.10 +

                location * 0.10 +

                70 * 0.15

            )


            results.append({

                "job": job.to_dict(),

                "match_score": final_score,

                "matched_skills": matched

            })


        return sorted(
            results,
            key=lambda x:x["match_score"],
            reverse=True
        )