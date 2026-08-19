from app.ai.llm import LocalLLM


class ProjectCoach:
    """
    AI coaching for a practical, gap-closing project the candidate is
    actively building - the mechanism that turns a skill-gap
    recommendation (app/ai/skill_gap.py) into real, defensible evidence.

    Four grounded uses of the local LLM, all via LocalLLM (same client
    as resume/cover-letter/interview-prep generation, same timeout/
    graceful-degradation behavior):

    - ``plan()``: a concrete, day-by-day starting plan with checkpoints
      for a newly started project - the "how do I even begin" answer,
      grounded only in the project's own title/description.
    - ``ask()``: open-ended coaching (explain a concept, walk through a
      step, help debug an error). This is exactly the kind of task an
      LLM is suited for - free-form technical explanation - unlike
      skill-gap recommendations (app/ai/skill_gap.py) or CV strength
      analysis (app/ai/cv_strength.py), which stay zero-LLM because
      they make factual claims that must not be hallucinated.
    - ``review()``: honest feedback on work the candidate actually
      pasted in (code, config, notes, logs) - reviews only what's
      actually submitted, never claims to have seen more than that.
    - ``draft_cv_bullet()``: grounded ONLY in the project's own recorded
      title/description/notes - never the wider candidate profile, and
      never called unless the project's status is already "Verified"
      (enforced by the caller, app/web/routes.py). The prompt is
      explicit that this is personal-project work, not professional
      experience, and the result is always review-only: nothing here
      writes to profiles/profile.json.
    """

    def __init__(self):
        self.ai = LocalLLM()

    def plan(self, project):
        prompt = f"""
You are an experienced, encouraging technical mentor helping a
cybersecurity/IT candidate start a practical, evidence-building project.

Project title:
{project['title']}

Project description:
{project['description']}

Write a short, concrete, day-by-day starting plan (aim for the shortest
realistic number of days - most of these projects should take from a
few hours up to about a week, not longer). For each day/step, include:
- what to actually do that day
- a checkpoint the candidate can use to verify they did it correctly

IMPORTANT RULES:
- Be specific: real tools, real commands/configuration where relevant.
- Do NOT claim the candidate has already done any of this.
- Do NOT invent facts about tools/platforms you're not confident about.
- Keep it practical and actionable, not a generic essay - a numbered
  Day 1 / Day 2 / ... structure is ideal.
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
                "(local Ollama did not respond)."
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
- Review ONLY what was actually submitted above. Do not assume
  anything about the project beyond what's shown.
- Be honest and specific: point out real issues (security weaknesses,
  bugs, bad practices) as well as what's done well.
- Do NOT claim the project is complete or correct if you can't verify
  that from what was submitted.
- Do NOT invent facts about tools/platforms you're not confident about.
- Keep feedback focused and actionable.
"""

        response = self.ai.ask(
            prompt,
            system=(
                "You are a practical, hands-on technical mentor for "
                "cybersecurity and IT projects, reviewing real "
                "submitted work honestly."
            ),
        )

        if response is None:
            raise RuntimeError(
                "AI project coaching is unavailable "
                "(local Ollama did not respond)."
            )

        return response.strip()

    def ask(self, project, question):
        prompt = f"""
You are an experienced, encouraging technical mentor helping a
cybersecurity/IT candidate complete a practical, evidence-building
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
- Answer only the technical question asked. Be specific and practical -
  real commands, real configuration, real troubleshooting steps where
  relevant.
- Do NOT claim the candidate has completed anything they haven't told
  you about.
- Do NOT invent facts about tools/platforms you're not confident about -
  say so if you're unsure, rather than guessing confidently.
- Keep the answer focused and actionable, not a generic essay.
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
                "(local Ollama did not respond)."
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
- Base the bullet ONLY on the project title/description/notes above.
- Do NOT invent tools, outcomes, metrics, or details not mentioned.
- Do NOT imply this was professional/employment experience - it is a
  personal project. If a label is needed, use "Personal Project" (or
  "Home Lab"/"Academic Project" if the description says so).
- Return ONLY the single bullet point text - no heading, no markdown,
  no explanation, no quotation marks around it.
- Keep it to one sentence, resume-appropriate, achievement-oriented
  wording grounded strictly in what's described above.
"""

        response = self.ai.ask(
            prompt,
            system="You are an expert, honest resume writer.",
        )

        if response is None:
            raise RuntimeError(
                "AI CV-bullet drafting is unavailable "
                "(local Ollama did not respond)."
            )

        return response.strip().strip('"')
