class SuitabilityEngine:

    def evaluate(self, job, profile):

        return {
            "overall_score": 0,
            "role_score": 0,
            "skill_score": 0,
            "experience_score": 0,
            "education_score": 0,
            "location_score": 0,
            "growth_score": 0,
            "recommendation": "",
            "strengths": [],
            "missing_skills": [],
            "reasoning": []
        }