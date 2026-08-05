import json



class TargetScorer:


    def __init__(self):

        with open(
            "config/job_targets.json",
            "r"
        ) as file:

            self.targets = json.load(file)



    def score(
        self,
        job
    ):

        title = job.get(
            "title",
            ""
        ).lower()


        score = 0



        for role in self.targets["priority_roles"]:

            if role.lower() in title:

                score += 40



        for role in self.targets["career_bridge_roles"]:

            if role.lower() in title:

                score += 25



        for role in self.targets["ignore_roles"]:

            if role.lower() in title:

                score -= 50



        return max(
            score,
            0
        )