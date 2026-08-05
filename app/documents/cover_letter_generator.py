from app.ai.llm import LocalLLM



class CoverLetterGenerator:

    def __init__(self):
        self.llm = LocalLLM()

    def generate(self, profile, job):

        prompt = f"""
You are an experienced career coach.

Write a professional cover letter.

Candidate Information

Education:
{", ".join(profile["education"])}

Skills:
{", ".join(profile["skills"])}

Target Roles:
{", ".join(profile["target_roles"])}

Location:
{profile["location"]}

Job Information

Job Title:
{job["title"]}

Company:
{job["company"]}

Job Description:
{job["description"]}

Requirements

- Professional tone
- Approximately 250-350 words
- Mention relevant skills naturally
- Explain why the candidate fits the role
- End with a polite closing
- Do NOT invent experience that wasn't provided
"""

        return self.llm.ask(prompt)