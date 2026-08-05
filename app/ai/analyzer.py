from app.ai.llm import LocalLLM


class JobAnalyzer:

    def __init__(self):
        self.llm = LocalLLM()

    def analyze(self, job, profile, score):

        strengths = []
        missing = []

        description = job["description"].lower()

        for skill in profile["skills"]:

            if skill.lower() in description:
                strengths.append(skill)
            else:
                missing.append(skill)

        prompt = f"""
You are a senior cybersecurity career coach.

Candidate profile

Education:
{", ".join(profile["education"])}

Skills:
{", ".join(profile["skills"])}

Target roles:
{", ".join(profile["target_roles"])}

Job Title:
{job["title"]}

Company:
{job["company"]}

Job Description:
{job["description"]}

Calculated Match Score:
{score}%

Write a professional analysis in 3-5 sentences explaining:
- why the candidate matches,
- which strengths to highlight,
- which missing skills should be improved,
- whether they should apply.
"""

        ai_analysis = self.llm.ask(prompt)

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

            "recommendation": recommendation,

            "ai_analysis": ai_analysis

        }