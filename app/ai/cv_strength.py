"""
Layer 1: general CV/profile strength analysis - job-independent.

This runs *before* any specific job is considered (see
docs/PRODUCT_VISION.md's "Final product flow"): it looks at the profile
as a whole and answers "is this CV strong on its own terms", not "does
this CV match posting X". Layer 2 (job-specific skill-gap analysis,
`app/ai/skill_gap.py`) builds on top of this once a job is selected.

Deterministic, zero LLM calls - same reasoning as `app/ai/skill_gap.py`:
this produces claims about the user's own CV ("this skill has no
evidence"), and those claims need to be reproducible and explainable,
not generated fresh each time.

Reuses the word-boundary matching helpers from `app/ai/skill_gap.py`
rather than a third independent copy - both modules live in the same
`app/ai` package and this is genuinely the same generic utility, unlike
the deliberate decoupling from `app/search/v2/matching/signals.py`
(a different, pipeline-owned module).
"""

import re

from app.ai.skill_gap import SKILL_CATALOG, _contains_any


# =============================================================
# Skill proficiency
#
# An automatic proficiency signal computed from what's already in
# profiles/profile.json (experience text, certifications) PLUS any
# Verified practical projects (app/database/project_tracker.py,
# app/services/project_service.py) - the strongest evidence tier,
# since it represents real, produced work (GitHub repo, README,
# findings), not just a claim. This avoids treating skills as simple
# present/absent: a skill named in a certification, demonstrated in
# experience, or backed by a verified project is a materially
# different claim than one that only appears in the bare skills list.
#
# What's still not built: an in-between "In Progress" contribution to
# proficiency, or a skill fading back down if evidence is later
# removed - level is always recomputed fresh from current data, not a
# persistent score that accumulates independently of the underlying
# evidence. See NEXT_TASKS.md.
# =============================================================

def _evaluate_skill(
    skill,
    experience_entries,
    certifications_text,
    has_verified_project=False,
):
    """
    Returns (level, evidence_text) for one profile skill.

    Level and evidence text are computed together (not separately) so
    they can never contradict each other - e.g. a skill that reaches
    "Advanced" only because it's named in a certification, with zero
    experience mentions, must say so plainly rather than implying it
    was demonstrated on the job.
    """

    mention_count = sum(
        1 for entry in experience_entries
        if _contains_any(entry, [skill])
    )
    has_certification = _contains_any(certifications_text, [skill])

    if has_verified_project:
        level = "Advanced"
        evidence = (
            "Backed by a verified practical project - real, produced "
            "evidence. See your Projects page."
        )
    elif mention_count >= 2:
        level = "Advanced"
        evidence = "Demonstrated in multiple experience entries."
    elif mention_count == 1 and has_certification:
        level = "Advanced"
        evidence = "Demonstrated in your experience and backed by a certification."
    elif has_certification:
        level = "Advanced"
        evidence = "Backed by a certification, but not demonstrated in an experience entry."
    elif mention_count == 1:
        level = "Intermediate"
        evidence = "Demonstrated in one experience entry."
    else:
        level = "Basic"
        evidence = "Only listed - not demonstrated in your experience or certifications."

    return level, evidence


# =============================================================
# Quantified achievements
#
# A heuristic, not a real NLP classifier: an experience description
# that contains a digit is treated as at least weakly quantified
# ("reduced incidents by 30%", "supported 200+ users", "8-person
# team"). Deliberately permissive - the goal is to flag descriptions
# with *zero* numbers at all, which are the clearest case of "purely
# generic wording", not to grade quantification quality.
# =============================================================

_HAS_DIGIT = re.compile(r"\d")


def _is_quantified(description):
    return bool(_HAS_DIGIT.search(str(description or "")))


def _is_thin(description):
    return len(str(description or "").strip()) < 40


def _find_catalog_entry(skill_text):
    """
    Match a profile skill string back to its SKILL_CATALOG key, if any -
    lets a "weakly evidenced" finding carry the same real, curated
    what/where/how/time recommendation Layer 2 (app/ai/skill_gap.py)
    already uses for job-specific gaps, instead of a bare "add an
    example" line with no concrete path.
    """

    for key, entry in SKILL_CATALOG.items():
        if _contains_any(skill_text, entry["aliases"]):
            return key, entry

    return None, None


# =============================================================
# Main entry point
# =============================================================

def analyze_cv_strength(profile, verified_skill_keys=None):
    """
    General, job-independent CV/profile strength analysis.

    ``verified_skill_keys``: skill_key values (app.ai.skill_gap.SKILL_CATALOG
    keys) with at least one Verified project - see
    app.services.project_service.ProjectService.verified_skill_keys().
    Optional so this function stays usable/testable without the
    project-tracking layer.

    Returns a dict shaped for direct template rendering:

    {
        "strengths": [str, ...],
        "weaknesses": [ {category, message}, ... ],  # highest-value first, capped
        "skills": [ {skill, level, evidence}, ... ],
        "summary": {...},
    }
    """

    profile = profile or {}
    verified_skill_keys = verified_skill_keys or set()
    skills = [str(skill) for skill in profile.get("skills", []) or []]
    experience = profile.get("experience", []) or []
    certifications = profile.get("certifications", []) or []
    certifications_text = " ".join(str(cert) for cert in certifications)

    experience_descriptions = [
        str(item.get("description", "")) if isinstance(item, dict) else str(item)
        for item in experience
    ]

    # ---------------------------------------------------------
    # Per-skill evidence / proficiency
    # ---------------------------------------------------------

    skill_entries = []
    matched_verified_keys = set()

    for skill in skills:
        has_verified_project = False

        for key in verified_skill_keys:
            entry = SKILL_CATALOG.get(key)

            if entry and _contains_any(skill, entry["aliases"]):
                has_verified_project = True
                matched_verified_keys.add(key)

        level, evidence = _evaluate_skill(
            skill,
            experience_descriptions,
            certifications_text,
            has_verified_project,
        )

        skill_entries.append({
            "skill": skill,
            "level": level,
            "evidence": evidence,
        })

    # A verified project can exist for a skill that isn't in the
    # profile's declared skills list at all yet - real, produced
    # evidence for a genuinely new capability shouldn't be invisible
    # just because the skills list hasn't been updated.
    for key in verified_skill_keys - matched_verified_keys:
        entry = SKILL_CATALOG.get(key)

        if not entry:
            continue

        skill_entries.append({
            "skill": entry["display"],
            "level": "Advanced",
            "evidence": (
                "Backed by a verified practical project, but not yet "
                "added to your profile's skills list - consider adding "
                f"{entry['display']} explicitly."
            ),
        })

    basic_unevidenced = [
        entry for entry in skill_entries if entry["level"] == "Basic"
    ]
    advanced_skills = [
        entry for entry in skill_entries if entry["level"] == "Advanced"
    ]

    # ---------------------------------------------------------
    # Experience quality
    # ---------------------------------------------------------

    quantified_count = sum(
        1 for description in experience_descriptions
        if _is_quantified(description)
    )
    thin_entries = [
        item for item, description in zip(experience, experience_descriptions)
        if _is_thin(description)
    ]

    # ---------------------------------------------------------
    # Strengths (surfaced first, per the product spec)
    # ---------------------------------------------------------

    strengths = []

    if advanced_skills:
        top_names = ", ".join(entry["skill"] for entry in advanced_skills[:5])
        strengths.append(
            f"Strong, demonstrated evidence for: {top_names}."
        )

    if certifications:
        strengths.append(
            f"{len(certifications)} certification(s) listed, "
            "reinforcing your claimed skills."
        )

    if quantified_count:
        strengths.append(
            f"{quantified_count} of {len(experience)} experience "
            "entries include a measurable detail (numbers, scope, or "
            "scale) rather than purely generic wording."
        )

    if not strengths:
        strengths.append(
            "Your profile has the basic structure in place - skills, "
            "experience, and education are all present."
        )

    # ---------------------------------------------------------
    # Weaknesses, prioritized and capped - do not overwhelm
    # ---------------------------------------------------------

    weaknesses = []

    for entry in basic_unevidenced[:3]:
        catalog_key, catalog_entry = _find_catalog_entry(entry["skill"])

        weakness = {
            "category": "skill_evidence",
            "skill": entry["skill"],
            "message": (
                f"{entry['skill']} is already on your profile - the "
                "missing piece is practical evidence."
            ),
        }

        if catalog_entry:
            weakness["skill_key"] = catalog_key
            weakness["recommendation"] = {
                "certifications": catalog_entry.get("certifications", []),
                "courses": catalog_entry.get("courses", []),
                "projects": catalog_entry.get("projects", []),
                "effort_days": catalog_entry.get("effort_days"),
            }
        else:
            weakness["message"] += (
                " Consider adding a specific example, or a small "
                "project, if you have relevant experience."
            )

        weaknesses.append(weakness)

    for item, description in list(zip(experience, experience_descriptions))[:5]:
        if not _is_quantified(description):
            title = item.get("title", "this role") if isinstance(item, dict) else "this role"
            weaknesses.append({
                "category": "quantification",
                "message": (
                    f"Your \"{title}\" entry has no measurable detail "
                    "(numbers, scale, or scope) - a specific figure "
                    "(e.g. \"monitored 50+ endpoints\", \"reduced "
                    "ticket backlog by 20%\") is more convincing than "
                    "a general description."
                ),
            })
            if len(weaknesses) >= 5:
                break

    if not certifications:
        weaknesses.append({
            "category": "certifications",
            "message": (
                "No certifications are listed. A relevant, realistically "
                "achievable certification can strengthen your CV, but "
                "only add one you've actually completed."
            ),
        })

    if not profile.get("projects"):
        weaknesses.append({
            "category": "projects",
            "message": (
                "No personal projects or GitHub evidence are listed. "
                "For candidates with limited professional experience, "
                "a small, honestly-labeled project (Personal Project, "
                "Home Lab, Academic Project) can meaningfully "
                "strengthen a CV - but never label one as professional "
                "employment experience."
            ),
        })

    # Highest-value first, then cap so the user isn't overwhelmed - see
    # docs/PRODUCT_VISION.md's "Do NOT overwhelm the user."
    weaknesses = weaknesses[:5]

    summary = {
        "skills_total": len(skills),
        "skills_advanced": len(advanced_skills),
        "skills_basic_unevidenced": len(basic_unevidenced),
        "certifications_total": len(certifications),
        "experience_entries": len(experience),
        "experience_quantified": quantified_count,
        "experience_thin": len(thin_entries),
    }

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "skills": skill_entries,
        "summary": summary,
    }
