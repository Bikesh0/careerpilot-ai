from app.ai.llm import LocalLLM


class JobAnalyzer:

    def __init__(self):
        self.llm = LocalLLM()

    def _format_education(self, education):
        """
        Convert structured education entries into readable text.
        Supports both dictionaries and plain strings.
        """

        formatted = []

        for item in education or []:

            if isinstance(item, dict):

                degree = item.get("degree", "")
                school = item.get("school", "")
                dates = item.get("dates", "")

                parts = []

                if degree:
                    parts.append(degree)

                if school:
                    parts.append(school)

                if dates:
                    parts.append(f"({dates})")

                if parts:
                    formatted.append(" - ".join(parts))

            else:

                value = str(item).strip()

                if value:
                    formatted.append(value)

        return formatted

    def _format_target_roles(self, target_roles):
        """
        Safely format target roles.
        The profile currently does not require target_roles,
        so an empty list is acceptable.
        """

        formatted = []

        for role in target_roles or []:

            if isinstance(role, dict):

                title = role.get("title", "")

                if title:
                    formatted.append(str(title))

            else:

                value = str(role).strip()

                if value:
                    formatted.append(value)

        return formatted

    def analyze(self, job, profile, score):

        strengths = []
        missing = []

        description = str(
            job.get("description", "")
        ).lower()

        profile_skills = profile.get(
            "skills",
            []
        )

        for skill in profile_skills:

            skill_text = str(skill).strip()

            if not skill_text:
                continue

            if skill_text.lower() in description:

                strengths.append(skill_text)

            else:

                missing.append(skill_text)

        education = self._format_education(
            profile.get("education", [])
        )

        target_roles = self._format_target_roles(
            profile.get("target_roles", [])
        )

        education_text = ", ".join(
            education
        )

        skills_text = ", ".join(
            str(skill)
            for skill in profile_skills
        )

        target_roles_text = ", ".join(
            target_roles
        )

        if not target_roles_text:
            target_roles_text = (
                "Cybersecurity, Information Security, "
                "SOC, Cloud Security, Linux/Systems"
            )

        prompt = f"""
You are a senior cybersecurity career coach.

Candidate profile

Education:
{education_text}

Skills:
{skills_text}

Target roles:
{target_roles_text}

Job Title:
{job.get("title", "")}

Company:
{job.get("company", "")}

Job Location:
{job.get("location", "")}

Job Description:
{job.get("description", "")}

Calculated Match Score:
{score}%

Write a professional analysis in 3-5 sentences explaining:

- why the candidate matches,
- which strengths to highlight,
- which missing skills should be improved,
- whether they should apply.

Do not invent experience, qualifications, certifications, or skills
that are not present in the candidate profile.
"""

        ai_analysis = self.llm.ask(prompt)

        if score >= 80:

            recommendation = "Strong match - Apply"

        elif score >= 60:

            recommendation = "Good match - Consider applying"

        else:

            recommendation = "Low match - Improve skills first"

        return {

            "job_title": job.get(
                "title",
                ""
            ),

            "company": job.get(
                "company",
                ""
            ),

            "match_score": score,

            "strengths": strengths[:5],

            "missing_skills": missing[:5],

            "recommendation": recommendation,

            "ai_analysis": ai_analysis

        }