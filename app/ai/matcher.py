class JobMatcher:

    def calculate_score(self, job, profile):

        text = job.description.lower()

        score = 0

        for skill in profile["skills"]:
            if skill.lower() in text:
                score += 10

        return score


    def rank_jobs(self, jobs, profile):

        results = []

        for job in jobs:
            score = self.calculate_score(job, profile)

            results.append({
                "job": job.to_dict(),
                "match_score": score
            })

        return sorted(
            results,
            key=lambda x: x["match_score"],
            reverse=True
        )