import json
import re

from app.ai.ai_engine import AIEngine


class ProfileExtractor:

    def __init__(self):

        self.ai = AIEngine()

    def extract(self, cv_text):

        prompt = f"""

Convert the following CV into JSON.

Return ONLY valid JSON.

Format:

{{
    "name":"",
    "email":"",
    "phone":"",
    "location":"",
    "linkedin":"",
    "summary":"",
    "skills":[],
    "experience":[],
    "education":[],
    "certifications":[]
}}

CV:

{cv_text}

"""

        response = self.ai.ask(

            "You extract structured resume data.",

            prompt

        )

        if response is None:
            raise RuntimeError(
                "CV extraction is unavailable "
                "(local Ollama did not respond)."
            )

        # The model sometimes wraps its JSON in a Markdown code fence
        # or adds surrounding text despite being asked not to - pull
        # out the first {...} block rather than assuming the response
        # is bare JSON.
        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise ValueError(
                "AI did not return valid JSON for the CV."
            )

        return json.loads(match.group())