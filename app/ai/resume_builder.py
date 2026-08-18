import json
import re

from app.ai.llm import LocalLLM


class ResumeBuilder:

    def __init__(self):

        self.ai = LocalLLM()

    def build(self, profile, job):

        prompt = f"""
You are an expert ATS resume writer.

Rewrite the candidate's resume for THIS job.

IMPORTANT:
Return ONLY ONE valid JSON object.
Do not explain.
Do not use markdown.
Do not wrap the JSON in ```.

Return exactly:

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
            prompt,
            system="You are an ATS resume expert.",
        )

        if response is None:
            raise RuntimeError(
                "AI resume generation is unavailable "
                "(local Ollama did not respond)."
            )

        print("\n========== AI RESPONSE ==========")
        print(response)
        print("=================================\n")

        # Extract JSON from response
        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise Exception(
                "AI did not return valid JSON."
            )

        json_text = match.group()

        return json.loads(json_text)