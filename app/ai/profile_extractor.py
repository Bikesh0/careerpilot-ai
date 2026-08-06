import json

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

        return json.loads(response)