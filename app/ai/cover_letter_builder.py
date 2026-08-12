from app.ai.ai_engine import AIEngine


class CoverLetterBuilder:

    def __init__(self):

        self.ai = AIEngine()

    def build(self, profile, job):

        prompt = f"""
Write a professional cover letter for this job application.

IMPORTANT RULES:

- Return ONLY the actual cover letter.
- Do NOT write an introduction explaining what you are doing.
- Do NOT write a conclusion explaining the letter.
- Do NOT use markdown.
- Do NOT use headings such as "Cover Letter".
- Do NOT use placeholders.
- Do NOT say "Here is the cover letter".
- Do NOT ask the candidate for more information.
- Do NOT invent experience, skills, education or certifications.
- Use only information contained in the candidate profile.
- Keep it concise: approximately 250-350 words.
- Address it to "Dear Hiring Manager,".
- End with "Sincerely," followed by the candidate's name.

The letter should:
1. Clearly state the position being applied for.
2. Explain why the candidate is relevant to the position.
3. Connect the candidate's real skills and experience to the job.
4. Show motivation for the company/role without inventing company-specific facts.
5. Finish professionally.

CANDIDATE PROFILE:

{profile}

JOB:

Title: {job.title}

Company: {job.company}

Location: {job.location}

Description:

{job.description}
"""

        return self.ai.ask(
            "You are an expert professional cover letter writer.",
            prompt
        ).strip()