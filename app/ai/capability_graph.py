"""
A small, hand-curated map of which SKILL_CATALOG entries are adjacent
to which others - e.g. Docker experience is a meaningful (if partial)
head start on Kubernetes, AWS experience is a head start on IAM/cloud
security.

Deliberately not exhaustive and not derived from any external taxonomy:
covering every one of SKILL_CATALOG's ~55 entries with "genuine"
relationships would either take real domain research per pair (out of
scope here) or produce noisy, made-up-feeling connections. This starts
with the relationships explicitly worth encoding - the ones a human
career advisor would actually say out loud - and is meant to grow by
hand over time, the same way SKILL_CATALOG itself does (see
app/ai/skill_gap.py's module docstring).

Each key is a SKILL_CATALOG key; each value is a list of SKILL_CATALOG
keys it's a meaningful, transferable head start toward. The relationship
is directional (Docker -> Kubernetes is a real head start; the reverse
is a much weaker claim) and intentionally not symmetric.
"""

CAPABILITY_GRAPH = {
    "linux": ["networking", "bash scripting"],
    "networking": ["siem", "firewall", "ids/ips"],
    "docker": ["kubernetes", "ci/cd"],
    "kubernetes": ["cloud security"],
    "python": ["ci/cd", "sast"],
    "aws": ["iam", "cloud security", "cloud security"],
    "azure": ["active directory", "iam"],
    "google cloud": ["iam", "cloud security"],
    "terraform": ["infrastructure as code", "ci/cd"],
    "iam": ["cloud security", "active directory"],
    "siem": ["detection engineering", "incident response"],
    "incident response": ["digital forensics", "soc operations"],
    "vulnerability management": ["penetration testing", "sast"],
    "sast": ["dast", "sca", "secrets management"],
    "ci/cd": ["infrastructure as code", "secrets management"],
    "active directory": ["iam"],
    "compliance and governance": ["soc 2", "iso 42001"],
}


def related_skills(skill_key):
    """
    SKILL_CATALOG keys that ``skill_key`` is a meaningful, transferable
    head start toward. Deduplicated; empty list if nothing is mapped.
    """

    seen = []

    for key in CAPABILITY_GRAPH.get(skill_key, []):
        if key not in seen:
            seen.append(key)

    return seen


def transferable_predecessors(skill_key):
    """
    The inverse of ``related_skills``: SKILL_CATALOG keys that are a
    meaningful, transferable head start *toward* ``skill_key``. Used to
    answer "the job wants X, which of the candidate's real skills is a
    head start toward X" - e.g. transferable_predecessors("kubernetes")
    includes "docker", since CAPABILITY_GRAPH maps docker -> kubernetes.
    """

    return [
        key
        for key, targets in CAPABILITY_GRAPH.items()
        if skill_key in targets
    ]
