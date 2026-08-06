import json

from app.ai.ai_engine import AIEngine


class ResumeBuilder:

    def __init__(self):

        self.ai = AIEngine()

    def build(self, profile, job):

        prompt = f"""
You are an expert ATS resume writer.

Rewrite the candidate's resume for THIS job.

Rules:

- Never invent experience.
- Never invent certifications.
- Never invent education.
- Never invent skills.
- Improve wording.
- Prioritize relevant experience.
- Keep ATS friendly.
- Return ONLY valid JSON.

Return this format:

{{
    "summary":"",
    "skills":[],
    "experience":[]
}}

Candidate Profile:

{json.dumps(profile, indent=2)}

Job Title:

{job.title}

Company:

{job.company}

Location:

{job.location}

Job Description:

{job.description}
"""

        response = self.ai.ask(

            "You are an ATS resume expert.",

            prompt

        )

        return json.loads(response)