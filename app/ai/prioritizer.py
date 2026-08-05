class JobPrioritizer:


    def prioritize(self, results):

        for job in results:

            score = job["match_score"]


            if score >= 80:

                job["priority_group"] = "APPLY TODAY"


            elif score >= 65:

                job["priority_group"] = "APPLY THIS WEEK"


            else:

                job["priority_group"] = "SKILL BUILDING"


        return sorted(
            results,
            key=lambda x: x["match_score"],
            reverse=True
        )