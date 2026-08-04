class JobAnalyzer:


    def analyze(self, job, profile, score):

        strengths = []

        missing = []


        description = job["description"].lower()


        for skill in profile["skills"]:

            if skill.lower() in description:
                strengths.append(skill)


            else:
                missing.append(skill)


        if score >= 80:
            recommendation = "Strong match - Apply"

        elif score >= 60:
            recommendation = "Good match - Consider applying"

        else:
            recommendation = "Low match - Improve skills first"


        return {

            "job_title": job["title"],

            "company": job["company"],

            "match_score": score,

            "strengths": strengths[:5],

            "missing_skills": missing[:5],

            "recommendation": recommendation

        }