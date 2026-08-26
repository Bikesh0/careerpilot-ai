from app.ai.llm import LocalLLM


# Project coaching can require substantially longer responses than
# short AI features. Keep the longer timeout local to this feature
# instead of slowing down the rest of CareerPilot's AI functionality.
PROJECT_COACH_TIMEOUT = 180


class ProjectCoach:
    """
    AI coaching for a practical, gap-closing project the candidate is
    actively building - the mechanism that turns a skill-gap
    recommendation (app/ai/skill_gap.py) into real, defensible evidence.

    Four grounded uses of the local LLM, all via LocalLLM:

    - plan(): creates a concrete, day-by-day plan based only on the
      project's title and description.
    - ask(): answers technical questions about the project.
    - review(): reviews only work actually submitted by the candidate.
    - draft_cv_bullet(): creates one CV bullet using only the project's
      recorded title, description, and notes.

    Project coaching uses a longer Ollama timeout because local LLM
    generation can be significantly slower for detailed planning and
    technical coaching requests.
    """

    def __init__(self):
        self.ai = LocalLLM(timeout=PROJECT_COACH_TIMEOUT)

    def plan(self, project):
        prompt = f"""
You are an experienced, practical technical mentor helping a
cybersecurity/IT candidate turn an existing practical project into
strong, defensible career evidence.

Project title:
{project['title']}

Project description:
{project['description']}

IMPORTANT CONTEXT:
The project described above may already exist or already be partially
developed. Do NOT assume the candidate is starting from zero.

Your job is to create a short, practical plan for the NEXT useful steps
needed to turn this project into clear evidence of the target skill.

For each day/step, include:
- what to actually do
- a concrete checkpoint to verify the work
- what evidence should be saved or documented

If the project already appears substantially developed, prioritize:
1. auditing the existing implementation,
2. identifying missing evidence,
3. improving documentation,
4. testing or validating the relevant functionality,
5. producing GitHub/README evidence,
6. preparing a defensible CV bullet.

Do NOT tell the candidate to recreate work that the description already
indicates exists.

Aim for the shortest realistic plan. Most projects should take from a
few hours up to about a week.

IMPORTANT RULES:
- Be specific and practical.
- Use real tools, commands, Git operations, configuration, or testing
  steps where relevant.
- Do NOT claim the candidate has already completed anything that is not
  stated in the project description.
- Do NOT invent tools, outcomes, metrics, or technical details.
- Do NOT assume technologies that are not supported by the project
  description.
- Focus on producing real, checkable evidence.
- Keep the response concise.
- Use a numbered Day 1 / Day 2 / Day 3 structure.
"""

        response = self.ai.ask(
            prompt,
            system=(
                "You are a practical, hands-on technical mentor for "
                "cybersecurity and IT projects. "
                "Your priority is producing realistic, checkable "
                "evidence rather than generic advice."
            ),
        )

        if response is None:
            raise RuntimeError(
                "AI project coaching is unavailable "
                "(local Ollama did not respond within the "
                f"{PROJECT_COACH_TIMEOUT}-second timeout)."
            )

        return response.strip()

    def review(self, project, submission):
        prompt = f"""
You are an experienced, encouraging technical mentor reviewing a
candidate's actual submitted work for a practical evidence-building
project.

Project title:
{project['title']}

Project description:
{project['description']}

The candidate's submitted work (code, configuration, notes, or logs -
review exactly what's below, nothing else):
{submission}

IMPORTANT RULES:
- Review ONLY what was actually submitted above.
- Do not assume anything about the project beyond what's shown.
- Be honest and specific.
- Point out real issues, security weaknesses, bugs, bad practices, and
  missing evidence where applicable.
- Also identify what is done well.
- Do NOT claim the project is complete or correct if you cannot verify
  that from the submitted material.
- Do NOT invent facts about tools or platforms.
- Give focused, actionable improvements.
- Where useful, identify what should be added to a README or GitHub
  repository as evidence.
"""

        response = self.ai.ask(
            prompt,
            system=(
                "You are a practical, hands-on technical mentor for "
                "cybersecurity and IT projects, reviewing real submitted "
                "work honestly."
            ),
        )

        if response is None:
            raise RuntimeError(
                "AI project coaching is unavailable "
                "(local Ollama did not respond within the "
                f"{PROJECT_COACH_TIMEOUT}-second timeout)."
            )

        return response.strip()

    def ask(self, project, question):
        prompt = f"""
You are an experienced, practical technical mentor helping a
cybersecurity/IT candidate complete a practical evidence-building
project.

Project title:
{project['title']}

Project description:
{project['description']}

Project notes so far (may be empty):
{project['notes'] or "(none yet)"}

The candidate's question:
{question}

IMPORTANT RULES:
- Answer only the technical question asked.
- Be specific and practical.
- Give real commands, configuration, testing, or troubleshooting steps
  where relevant.
- Do NOT claim the candidate has completed anything they have not told
  you about.
- Do NOT invent facts about tools or platforms.
- If something is uncertain, say so rather than guessing.
- Keep the answer focused and actionable.
"""

        response = self.ai.ask(
            prompt,
            system=(
                "You are a practical, hands-on technical mentor for "
                "cybersecurity and IT projects."
            ),
        )

        if response is None:
            raise RuntimeError(
                "AI project coaching is unavailable "
                "(local Ollama did not respond within the "
                f"{PROJECT_COACH_TIMEOUT}-second timeout)."
            )

        return response.strip()

    def draft_cv_bullet(self, project):
        prompt = f"""
Write ONE honest CV bullet point for a personal/practical project the
candidate has completed and verified.

Project title:
{project['title']}

Project description:
{project['description']}

Project notes (what was actually done):
{project['notes'] or "(no additional notes recorded)"}

IMPORTANT RULES:
- Base the bullet ONLY on the project title, description, and notes.
- Do NOT invent tools, outcomes, metrics, or details.
- Do NOT imply this was professional/employment experience.
- If a label is needed, use "Personal Project", "Home Lab", or
  "Academic Project" only when supported by the project information.
- Return ONLY the single bullet point.
- No heading.
- No markdown.
- No explanation.
- No quotation marks.
- Keep it to one sentence.
- Make it achievement-oriented but strictly factual.
"""

        response = self.ai.ask(
            prompt,
            system="You are an expert, honest resume writer.",
        )

        if response is None:
            raise RuntimeError(
                "AI CV-bullet drafting is unavailable "
                "(local Ollama did not respond within the "
                f"{PROJECT_COACH_TIMEOUT}-second timeout)."
            )

        return response.strip().strip('"')
