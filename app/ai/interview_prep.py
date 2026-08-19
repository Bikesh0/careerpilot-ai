import json
import re

from app.ai.llm import LocalLLM


class InterviewPrepBuilder:
    """
    Generates job-specific interview-preparation questions.

    Unlike app/ai/skill_gap.py and app/ai/cv_strength.py, this
    deliberately DOES use the local LLM (via LocalLLM, same as
    resume_builder.py/cover_letter_builder.py) - generating a set of
    plausible, well-phrased interview questions genuinely is a language
    -generation task, not a factual-recommendation task like a
    certification suggestion. The grounding rule from those other two
    builders still applies here: never invent experience for the
    candidate, and every question must be traceable to the real job
    description or the real profile.

    This is only ever called after app/web/routes.py has confirmed the
    application has actually reached interview stage - see
    INTERVIEW_STAGE_STATUSES in app/services/application_service.py.
    Interview prep proactively pushed for a job the user hasn't
    reached interview stage for would work against the product's
    stated "calm advisor, not pressure" principle.
    """

    def __init__(self):
        self.ai = LocalLLM()

    def build(self, profile, job, missing_skills=None):
        missing_skills = missing_skills or []

        prompt = f"""
You are an expert technical interview coach preparing a candidate for a
real upcoming interview.

IMPORTANT RULES:
- Base every question ONLY on the candidate profile and job description below.
- Do NOT invent experience, employers, achievements, or certifications for the candidate.
- Return ONLY one valid JSON object. Do not explain. Do not use markdown. Do not wrap the JSON in ```.

Return exactly this shape:
{{
    "technical_questions": ["...", "..."],
    "scenario_questions": ["...", "..."],
    "cv_questions": ["...", "..."],
    "project_questions": ["...", "..."],
    "explain_this_questions": ["...", "..."]
}}

Guidance for each list:
- technical_questions: 2-3 direct technical questions about skills this job requires that the candidate genuinely has, based on their profile.
- scenario_questions: 2-3 realistic "how would you troubleshoot/handle X" situational questions relevant to this specific role.
- cv_questions: 2-3 questions specifically about the candidate's actual listed experience entries below - ask them to explain a real decision or outcome from that experience.
- project_questions: 1-2 questions about any certifications or education in the candidate's profile below.
- explain_this_questions: 1-2 "explain this technology/concept in your own words" questions, focused on these specific skills the job mentions that may be a gap for this candidate: {", ".join(missing_skills) or "none identified - use a core skill from the job description instead"}. For each, briefly note in the question itself what a strong answer would cover, so the candidate can self-check their understanding.

Candidate Profile:
{json.dumps(profile, indent=2)}

Job Title:
{getattr(job, "title", "")}

Company:
{getattr(job, "company", "")}

Job Description:
{getattr(job, "description", "")}
"""

        response = self.ai.ask(
            prompt,
            system="You are an expert technical interview coach.",
        )

        if response is None:
            raise RuntimeError(
                "AI interview preparation is unavailable "
                "(local Ollama did not respond)."
            )

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise ValueError("AI did not return valid JSON.")

        parsed = json.loads(match.group())

        expected_keys = [
            "technical_questions",
            "scenario_questions",
            "cv_questions",
            "project_questions",
            "explain_this_questions",
        ]

        return {key: parsed.get(key, []) for key in expected_keys}
