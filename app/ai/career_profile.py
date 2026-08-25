"""
The "Living Career Profile": a single view of what the user's profile
actually demonstrates, and how, distinguishing evidence *kinds* rather
than collapsing everything into one proficiency number.

app/ai/cv_strength.py already computes a 3-tier proficiency
(Basic/Intermediate/Advanced) per profile skill. This module sits next
to it, not on top of it or instead of it - cv_strength.py answers "how
strong is this skill's evidence", this module answers the more specific
question the product spec asks for: "what *kind* of evidence exists for
this skill" - a course is not a job, a certification is not a verified
project. Both modules are deterministic and zero-LLM for the same
reason: these are claims about the user's own real profile data, and
must be reproducible and explainable, never a fresh guess per call.

Six evidence tiers, all sourced from data the app already legitimately
holds - profiles/profile.json (skills, experience, education,
certifications) and the project-tracking database
(app/database/project_tracker.py via app/services/project_service.py).
Nothing here infers or invents evidence; a skill with no matching
signal in any of these sources gets the weakest tier, KNOWS, not a
guess at something stronger.

- PROFESSIONAL_EXPERIENCE: named in a profile "experience" entry.
- CERTIFIED: named in the profile's certifications list.
- BUILT: backed by a Verified project (the strongest practical-evidence
  tier - real, produced work, not just a claim).
- PRACTICED: backed by a project that's Planned/In Progress/Completed
  but not yet Verified - real effort underway, not yet finished
  evidence.
- STUDIED: named in an education entry (degree/programme text) - the
  only source of "coursework" signal this profile format actually
  carries; there is no separate "completed courses" field to read, so
  this tier is deliberately conservative rather than invented.
- KNOWS: the skill is only in the bare skills list, with none of the
  above - the weakest, least-evidenced claim.

A skill can (and often should) carry more than one tier at once - e.g.
a certified skill also demonstrated in a work-experience entry is both
CERTIFIED and PROFESSIONAL_EXPERIENCE, which is a materially stronger
claim than either alone.
"""

from app.ai.skill_gap import SKILL_CATALOG, _contains_any

PROFESSIONAL_EXPERIENCE = "professional_experience"
CERTIFIED = "certified"
BUILT = "built"
PRACTICED = "practiced"
STUDIED = "studied"
KNOWS = "knows"

_TIER_LABELS = {
    PROFESSIONAL_EXPERIENCE: "Professional experience",
    CERTIFIED: "Certified",
    BUILT: "Built (verified project)",
    PRACTICED: "Practiced (project underway)",
    STUDIED: "Studied",
    KNOWS: "Knows (claimed only)",
}

# Weakest to strongest, used only to pick a single "headline" tier per
# skill for compact display - the full tier set is always available too.
_TIER_STRENGTH_ORDER = [
    KNOWS, STUDIED, PRACTICED, CERTIFIED, PROFESSIONAL_EXPERIENCE, BUILT,
]


def _strongest_tier(tiers):
    for candidate in reversed(_TIER_STRENGTH_ORDER):
        if candidate in tiers:
            return candidate
    return KNOWS


def _project_skill_keys_by_status(projects, statuses):
    return {
        project["skill_key"]
        for project in projects or []
        if project.get("status") in statuses and project.get("skill_key")
    }


def build_career_profile(profile, verified_skill_keys=None, projects=None):
    """
    ``profile``: the loaded profiles/profile.json dict.
    ``verified_skill_keys``: see
    app.services.project_service.ProjectService.verified_skill_keys().
    ``projects``: the full project list (ProjectService.get_all()) -
    used to also recognize PRACTICED (not-yet-verified) evidence and to
    build the continuity view. Optional so this stays testable without
    the project-tracking layer.

    Returns:
    {
        "skills": [ {skill, tiers: [...], headline_tier, labels: [...]} ],
        "continuity": {
            "in_progress": [ {id, skill_display, title, status}, ... ],
            "recently_built": [ {id, skill_display, title}, ... ],
        },
        "summary": {...},
    }
    """

    profile = profile or {}
    projects = projects or []
    verified_skill_keys = verified_skill_keys or set()

    skills = [str(skill) for skill in profile.get("skills", []) or []]
    experience = profile.get("experience", []) or []
    education = profile.get("education", []) or []
    certifications = profile.get("certifications", []) or []

    experience_text = " ".join(
        str(item.get("description", "")) if isinstance(item, dict) else str(item)
        for item in experience
    )
    education_text = " ".join(
        " ".join(str(value) for value in item.values())
        if isinstance(item, dict) else str(item)
        for item in education
    )
    certifications_text = " ".join(str(cert) for cert in certifications)

    practiced_keys = _project_skill_keys_by_status(
        projects, {"Planned", "In Progress", "Completed"}
    )

    skill_entries = []

    for skill in skills:
        tiers = set()

        if _contains_any(experience_text, [skill]):
            tiers.add(PROFESSIONAL_EXPERIENCE)

        if _contains_any(certifications_text, [skill]):
            tiers.add(CERTIFIED)

        if _contains_any(education_text, [skill]):
            tiers.add(STUDIED)

        for key in verified_skill_keys:
            entry = SKILL_CATALOG.get(key)
            if entry and _contains_any(skill, entry["aliases"]):
                tiers.add(BUILT)

        for key in practiced_keys:
            entry = SKILL_CATALOG.get(key)
            if entry and _contains_any(skill, entry["aliases"]):
                tiers.add(PRACTICED)

        if not tiers:
            tiers.add(KNOWS)

        headline = _strongest_tier(tiers)

        skill_entries.append({
            "skill": skill,
            "tiers": sorted(tiers, key=_TIER_STRENGTH_ORDER.index),
            "headline_tier": headline,
            "headline_label": _TIER_LABELS[headline],
            "labels": [_TIER_LABELS[tier] for tier in tiers],
        })

    # ---------------------------------------------------------
    # Continuity: what's already underway, so recommendations can
    # build on it instead of proposing a fresh start (see
    # app/ai/skill_gap.py's continuity handling, which reads this same
    # project list independently via routes.py).
    # ---------------------------------------------------------

    in_progress = [
        {
            "id": project["id"],
            "skill_display": project["skill_display"],
            "title": project["title"],
            "status": project["status"],
        }
        for project in projects
        if project.get("status") in ("Planned", "In Progress", "Completed")
    ]

    recently_built = [
        {
            "id": project["id"],
            "skill_display": project["skill_display"],
            "title": project["title"],
        }
        for project in projects
        if project.get("status") == "Verified"
    ]

    summary = {
        "skills_total": len(skill_entries),
        "professional_experience_count": sum(
            1 for entry in skill_entries
            if PROFESSIONAL_EXPERIENCE in entry["tiers"]
        ),
        "certified_count": sum(
            1 for entry in skill_entries if CERTIFIED in entry["tiers"]
        ),
        "built_count": sum(
            1 for entry in skill_entries if BUILT in entry["tiers"]
        ),
        "practiced_count": sum(
            1 for entry in skill_entries if PRACTICED in entry["tiers"]
        ),
        "knows_only_count": sum(
            1 for entry in skill_entries if entry["tiers"] == [KNOWS]
        ),
        "projects_in_progress": len(in_progress),
        "projects_verified": len(recently_built),
    }

    return {
        "skills": skill_entries,
        "continuity": {
            "in_progress": in_progress,
            "recently_built": recently_built,
        },
        "summary": summary,
    }
