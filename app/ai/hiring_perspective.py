"""
Three separate, deterministic views of the same job+profile pair,
corresponding to three real stages of a hiring funnel - ATS/keyword
screening, HR/recruiter review, and technical-manager evaluation.
Never blended into one score: each answers a genuinely different
question, and collapsing them would hide exactly the distinction the
product spec asks for (a candidate can be a strong technical fit while
the CV under-communicates it, or vice versa).

Deliberately reuses, not duplicates, what already exists:
- ATS perspective is a relabeled view of app.ai.skill_gap's own
  required/nice-to-have coverage - that IS a keyword/terminology
  alignment check already, just not framed as one.
- Technical-manager perspective is a relabeled view of
  app.ai.skill_gap's own per-skill "evidence" field (which already
  recognizes a Verified project or a skills-list+experience match as
  "demonstrated") - a Verified project or real experience entry is
  exactly what a technical manager would want to see, not just a
  claim, and skill_gap.py already computes that distinction correctly
  in one place.
- HR perspective is the only genuinely new logic here, and is kept
  strictly structural (title alignment, education presence, a stated
  experience-years requirement vs. how many experience entries the
  profile lists) - never an invented judgment about "credibility" or
  "professional presentation," which isn't something this app can
  honestly measure from the data it has.

Zero-LLM, for the same reproducibility/anti-hallucination reason as
app/ai/skill_gap.py and app/ai/cv_strength.py (see docs/AI.md).
"""

import re

from app.ai.skill_gap import _contains_any

# Same patterns as app/search/v2/matching/signals.py's
# extract_required_experience_years() - duplicated, not imported, to
# keep app/ai decoupled from the V2 search pipeline's internals (the
# same precedent app/ai/skill_gap.py's own independent normalizer
# already sets, documented in its module docstring).
_EXPERIENCE_YEAR_PATTERNS = [
    r"(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience",
    r"minimum\s+of\s+(\d+)\s+years?",
    r"at\s+least\s+(\d+)\s+years?",
    r"(\d+)\s*-\s*\d+\s+years?\s+(?:of\s+)?experience",
    r"(\d+)\s*\+\s*years?",
]

STRONG = "strong"
DEVELOPING = "developing"
EVIDENCE_NEEDED = "evidence_needed"

_LEVEL_LABELS = {
    STRONG: "Strong",
    DEVELOPING: "Developing",
    EVIDENCE_NEEDED: "Evidence needed",
}


def _extract_required_experience_years(text):
    text = str(text or "")
    matches = []

    for pattern in _EXPERIENCE_YEAR_PATTERNS:
        for value in re.findall(pattern, text, flags=re.IGNORECASE):
            try:
                matches.append(int(value))
            except (TypeError, ValueError):
                continue

    return max(matches) if matches else None


def _level_from_ratio(ratio):
    if ratio >= 0.7:
        return STRONG
    if ratio >= 0.35:
        return DEVELOPING
    return EVIDENCE_NEEDED


def _ats_perspective(skill_gap_analysis):
    required = skill_gap_analysis.get("required", [])

    if not required:
        return {
            "level": None,
            "label": "Not enough data",
            "detail": (
                "No structured requirements were reliably extracted "
                "from this posting, so an ATS-style keyword comparison "
                "isn't possible here."
            ),
        }

    matched = sum(1 for item in required if item["status"] == "matched")
    total = len(required)
    level = _level_from_ratio(matched / total)

    return {
        "level": level,
        "label": _LEVEL_LABELS[level],
        "detail": (
            f"{matched} of {total} required terms this posting uses "
            "also appear in your profile - the terminology overlap an "
            "automated keyword screen would look for."
        ),
    }


def _technical_perspective(skill_gap_analysis):
    """
    Reuses app.ai.skill_gap's own per-skill "evidence" field rather
    than re-deriving evidence strength independently: a matched
    required skill with evidence level "demonstrated" already means
    either a Verified project or both a skills-list AND an experience
    mention - exactly the bar a technical manager would look for, and
    computed once, correctly, in one place.
    """

    required = skill_gap_analysis.get("required", [])

    if not required:
        return {
            "level": None,
            "label": "Not enough data",
            "detail": (
                "No structured requirements were reliably extracted "
                "from this posting, so a technical-evidence comparison "
                "isn't possible here."
            ),
        }

    strongly_evidenced = sum(
        1 for item in required
        if item["status"] == "matched"
        and item.get("evidence", {}).get("level") == "demonstrated"
    )

    total = len(required)
    level = _level_from_ratio(strongly_evidenced / total)

    return {
        "level": level,
        "label": _LEVEL_LABELS[level],
        "detail": (
            f"{strongly_evidenced} of {total} required skills are "
            "backed by a Verified project or real experience entry - "
            "not just a claim in your skills list. That's the kind of "
            "proof a technical manager weighs most heavily."
        ),
    }


def _hr_perspective(profile, job):
    profile = profile or {}
    job_title = str(getattr(job, "title", "") or "")
    job_text = f"{job_title} {getattr(job, 'description', '') or ''}"

    target_titles = profile.get("target_titles", []) or []
    # _contains_any does contiguous word-boundary matching, so a target
    # title like "Security Engineer" already matches a job titled
    # "Senior Security Engineer" or "Cloud Security Engineer" via the
    # shared "security engineer" token sequence - no separate
    # word-splitting fallback needed.
    title_aligned = bool(job_title) and _contains_any(job_title, target_titles)

    experience_entries = profile.get("experience", []) or []
    has_education = bool(profile.get("education"))
    required_years = _extract_required_experience_years(job_text)

    signals_met = sum([
        title_aligned,
        bool(experience_entries),
        has_education,
    ])

    level = _level_from_ratio(signals_met / 3)

    detail_parts = []

    if title_aligned:
        detail_parts.append(
            "this posting's title broadly matches roles you're "
            "targeting"
        )
    else:
        detail_parts.append(
            "this posting's title doesn't clearly match your stated "
            "target roles - worth checking it's still the direction "
            "you want"
        )

    detail_parts.append(
        f"your profile lists {len(experience_entries)} experience "
        f"entr{'y' if len(experience_entries) == 1 else 'ies'}"
    )

    if has_education:
        detail_parts.append("relevant education is present")

    if required_years:
        detail_parts.append(
            f"this posting mentions {required_years}+ years of "
            "experience - review whether your entries communicate "
            "comparable depth, even if gained differently (projects, "
            "training, internships)"
        )

    return {
        "level": level,
        "label": _LEVEL_LABELS[level],
        "detail": ("; ".join(detail_parts) + ".").capitalize(),
    }


def build_hiring_perspective(profile, job, skill_gap_analysis):
    """
    Returns {"ats": {...}, "hr": {...}, "technical": {...}}, each
    {"level", "label", "detail"} - level is one of STRONG/DEVELOPING/
    EVIDENCE_NEEDED, or None when there wasn't enough extracted data to
    assess (never guessed). ``skill_gap_analysis`` must come from
    app.ai.skill_gap.analyze_skill_gap(profile, job) - both the ATS and
    technical views are relabeled projections of it, not independently
    recomputed.
    """

    return {
        "ats": _ats_perspective(skill_gap_analysis),
        "hr": _hr_perspective(profile, job),
        "technical": _technical_perspective(skill_gap_analysis),
    }
