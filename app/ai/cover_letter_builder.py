from app.ai.ai_engine import AIEngine


class CoverLetterBuilder:

    def __init__(self):

        self.ai = AIEngine()

    def build(self, profile, job):

        prompt = f"""
You are a professional career coach.

Write a modern ATS-friendly cover letter.

Rules:

- Use only information from the profile.
- Never invent experience.
- Never invent certifications.
- Keep it professional.
- Around 350 words.
- No placeholders.
- No markdown.

Candidate Profile

{profile}

Job

Title:
{job.title}

Company:
{job.company}

Location:
{job.location}

Description:

{job.description}
"""

        return self.ai.ask(

            "You are an expert cover letter writer.",

            prompt

        )