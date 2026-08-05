class DecisionEngine:


    def decide(
        self,
        score,
        missing_skills,
        job_title=""
    ):


        title = job_title.lower()



        # Junior roles need lower threshold

        junior_keywords = [

            "junior",
            "trainee",
            "intern",
            "graduate",
            "entry"

        ]



        is_junior = any(

            word in title

            for word in junior_keywords

        )



        if is_junior:


            if score >= 55:

                return {

                    "decision": "APPLY NOW",

                    "priority": "HIGH",

                    "reason":
                    "Good junior-level match. Skills and education align."

                }


            elif score >= 40:

                return {

                    "decision": "CONSIDER APPLYING",

                    "priority": "MEDIUM",

                    "reason":
                    "Potential junior match. Highlight transferable skills."

                }



        else:


            if score >= 75:

                return {

                    "decision": "APPLY NOW",

                    "priority": "HIGH",

                    "reason":
                    "Strong match with required skills."

                }


            elif score >= 55:

                return {

                    "decision": "CONSIDER APPLYING",

                    "priority": "MEDIUM",

                    "reason":
                    "Good potential match. Improve missing skills."

                }



        return {

            "decision": "SKILL BUILDING",

            "priority": "LOW",

            "reason":
            "Large skill gap compared with requirements."

        }