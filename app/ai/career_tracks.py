"""
Ranks a small, hand-curated set of cybersecurity/IT career tracks by
how well the user's actual profile fits each one, and (optionally) how
often each track's skills actually appear in job postings the app has
already, legitimately collected (never a new scrape performed just for
this - see docs/AI.md's research-source boundary).

Two components, kept separate and both shown, never blended into a
single opaque number presented as a probability:

- **Profile fit**: how much of a track's key skills the user's own
  Living Career Profile (app/ai/career_profile.py) actually
  demonstrates, weighted by evidence strength (a Verified project or
  professional experience counts far more than a bare "knows" claim).
- **Market signal**: how often a track's key skills actually appear
  across the job postings currently known to the app (whatever the
  last real search returned) - a real, if limited and session-scoped,
  demand signal, not an external market-research claim. None is shown
  (rather than a misleading 0%) when no job data is available at all.

Deliberately a small, curated track list, each mapped to a handful of
SKILL_CATALOG keys - the same "hand-curated over exhaustive" precedent
app/ai/capability_graph.py and app/ai/skill_gap.py's own SKILL_CATALOG
already set, for the same reason: a track-to-skill mapping asserted for
dozens of tracks without real labour-market research behind it would be
noise dressed up as intelligence.
"""

from app.ai.career_profile import (
    BUILT,
    CERTIFIED,
    KNOWS,
    PRACTICED,
    PROFESSIONAL_EXPERIENCE,
    STUDIED,
)
from app.ai.skill_gap import _contains_any, SKILL_CATALOG

# Tier -> weight used only for the profile-fit score below. Ordered the
# same as app/ai/career_profile.py's own strength ordering; KNOWS
# deliberately contributes almost nothing; a Verified project (BUILT)
# is worth the most, ahead of a bare experience mention.
_TIER_WEIGHT = {
    BUILT: 1.0,
    PROFESSIONAL_EXPERIENCE: 0.85,
    CERTIFIED: 0.7,
    PRACTICED: 0.55,
    STUDIED: 0.4,
    # A bare claim with no other evidence is still some signal - just
    # the weakest kind - so it isn't scored identically to a skill the
    # profile doesn't mention at all (weight 0, the default below).
    KNOWS: 0.15,
}

CAREER_TRACKS = {
    "soc_security_operations": {
        "display": "SOC / Security Operations",
        "skill_keys": [
            "siem", "incident response", "soc operations", "splunk",
            "networking", "linux",
        ],
    },
    "cybersecurity_analyst": {
        "display": "Cybersecurity / Information Security Analyst",
        "skill_keys": [
            "vulnerability management", "incident response",
            "compliance and governance", "siem", "linux",
        ],
    },
    "network_security": {
        "display": "Network Security",
        "skill_keys": [
            "networking", "firewall", "ids/ips", "vpn", "linux",
        ],
    },
    "penetration_testing": {
        "display": "Penetration Testing / Offensive Security",
        "skill_keys": [
            "penetration testing", "vulnerability management",
            "networking", "linux", "python",
        ],
    },
    "cloud_security": {
        "display": "Cloud Security",
        "skill_keys": [
            "cloud security", "aws", "azure", "google cloud", "iam",
            "infrastructure as code",
        ],
    },
    "devsecops": {
        "display": "DevSecOps / Security Engineering",
        "skill_keys": [
            "docker", "kubernetes", "ci/cd", "terraform",
            "infrastructure as code", "sast", "python",
        ],
    },
    "it_support_to_security": {
        "display": "IT Support -> Security (transition track)",
        "skill_keys": [
            "windows", "networking", "linux", "active directory",
            "powershell",
        ],
    },
}


def _profile_fit(track_skill_keys, skill_entries):
    """
    0-100: average, weighted evidence strength across the track's key
    skills, matched against the profile's skill list by catalog alias.
    A skill with no matching profile entry at all contributes 0.
    """

    if not track_skill_keys:
        return 0.0

    total = 0.0

    for key in track_skill_keys:
        entry = SKILL_CATALOG.get(key)
        if not entry:
            continue

        best_weight = 0.0

        for skill_entry in skill_entries:
            if _contains_any(skill_entry["skill"], entry["aliases"]):
                best_weight = max(
                    best_weight,
                    max(
                        (_TIER_WEIGHT.get(tier, 0.0) for tier in skill_entry["tiers"]),
                        default=0.0,
                    ),
                )

        total += best_weight

    return round(100 * total / len(track_skill_keys))


def _market_signal(track_skill_keys, job_texts):
    """
    0-100, or None if no job data was supplied at all - "no data" and
    "zero demand observed" must never be conflated. Fraction of the
    given job texts that mention at least one of the track's skills.
    """

    if not job_texts:
        return None

    if not track_skill_keys:
        return 0.0

    hits = 0

    for text in job_texts:
        aliases = [
            alias
            for key in track_skill_keys
            for alias in SKILL_CATALOG.get(key, {}).get("aliases", [])
        ]

        if _contains_any(text, aliases):
            hits += 1

    return round(100 * hits / len(job_texts))


def rank_career_tracks(career_profile, job_texts=None):
    """
    ``career_profile``: the dict from
    app.ai.career_profile.build_career_profile().
    ``job_texts``: optional list of "title description" strings from
    jobs the app already has (e.g. manager.latest_jobs) - real,
    session-scoped market signal, never a fresh external scrape
    performed just for this.

    Returns a list of tracks, strongest profile fit first, each:
    {"key", "display", "profile_fit", "market_signal", "matched_skills",
     "missing_skills"}
    """

    skill_entries = career_profile.get("skills", []) if career_profile else []

    ranked = []

    for key, track in CAREER_TRACKS.items():
        track_skill_keys = track["skill_keys"]

        matched_skills = []
        missing_skills = []

        for skill_key in track_skill_keys:
            entry = SKILL_CATALOG.get(skill_key)
            if not entry:
                continue

            demonstrated = any(
                _contains_any(skill_entry["skill"], entry["aliases"])
                for skill_entry in skill_entries
            )

            (matched_skills if demonstrated else missing_skills).append(
                entry["display"]
            )

        ranked.append({
            "key": key,
            "display": track["display"],
            "profile_fit": _profile_fit(track_skill_keys, skill_entries),
            "market_signal": _market_signal(track_skill_keys, job_texts),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        })

    ranked.sort(key=lambda item: item["profile_fit"], reverse=True)

    return ranked


# A track needs at least this share of its own key skills mentioned in
# a job's text before it's considered a real secondary family for that
# job - otherwise almost every posting would pick up a long tail of
# barely-relevant "secondary" families from a single incidental skill
# mention (e.g. a SOC posting mentioning "Linux" once shouldn't also
# get tagged "IT Support").
_SECONDARY_FAMILY_MIN_COVERAGE = 0.34


def classify_job_family(job):
    """
    Classifies a single job posting into a primary career family, and
    a secondary one when a second track's key skills are also
    substantially present (real jobs frequently span two related
    families - e.g. "Cloud Security Engineer" primarily Cloud Security,
    secondarily Security Engineering). Uses the same CAREER_TRACKS
    definitions rank_career_tracks() ranks against the *profile* -
    this is the inverse direction, ranked against the *job's own text*
    instead.

    Returns {"primary": {...}, "secondary": {...} | None}, each
    {"key", "display", "coverage", "matched_skills"} - "coverage" is
    the share (0-100) of the track's key skills this job's text
    mentions, not a hiring-relevance probability.
    """

    text = f"{getattr(job, 'title', '') or ''} {getattr(job, 'description', '') or ''}"

    scored = []

    for key, track in CAREER_TRACKS.items():
        track_skill_keys = track["skill_keys"]

        matched = [
            SKILL_CATALOG[skill_key]["display"]
            for skill_key in track_skill_keys
            if skill_key in SKILL_CATALOG
            and _contains_any(text, SKILL_CATALOG[skill_key]["aliases"])
        ]

        if not matched:
            continue

        scored.append({
            "key": key,
            "display": track["display"],
            "coverage": round(100 * len(matched) / len(track_skill_keys)),
            "matched_skills": matched,
        })

    if not scored:
        return {"primary": None, "secondary": None}

    scored.sort(key=lambda item: item["coverage"], reverse=True)

    primary = scored[0]
    secondary = None

    for candidate in scored[1:]:
        if (
            candidate["key"] != primary["key"]
            and candidate["coverage"] >= _SECONDARY_FAMILY_MIN_COVERAGE * 100
        ):
            secondary = candidate
            break

    return {"primary": primary, "secondary": secondary}
