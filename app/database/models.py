from dataclasses import dataclass


@dataclass
class Application:

    company: str
    title: str
    location: str
    source: str

    status: str

    applied_date: str

    job_url: str = ""

    resume_file: str = ""

    cover_letter_file: str = ""

    notes: str = ""


@dataclass
class Project:
    """
    A practical, gap-closing project the candidate is building to turn
    a skill-gap recommendation into real evidence.

    ``skill_key`` is the internal app.ai.skill_gap.SKILL_CATALOG key
    (e.g. "kubernetes"), not the display name - it's what lets
    app.ai.cv_strength recognize a Verified project as evidence for that
    skill. ``status`` must be one of PROJECT_STATUSES
    (app/database/project_tracker.py) - "Planned", "In Progress",
    "Completed", or "Verified". Never set automatically by anything
    other than an explicit user action - see docs/PRODUCT_VISION.md.
    """

    skill_key: str
    skill_display: str

    title: str
    description: str

    status: str

    created_date: str

    source_job_url: str = ""

    notes: str = ""

    cv_bullet: str = ""