"""
Classifies a job into one of five application-readiness tiers, so the
user gets a concrete "should I apply to this one" verdict instead of
having to mentally combine the Profile Match score and the Career Fit
& Growth page themselves.

Deliberately zero-LLM and deterministic, for the same reason
app/ai/skill_gap.py is: the verdict needs to be explainable ("why does
this say APPLY_STRETCH") and reproducible, not a fresh guess per call.
See docs/AI.md.

Five tiers (matching the product spec's own naming):

- APPLY_NOW: strong fit - either the Career Fit & Growth page's own
  "ready to apply" signal fired (every detected required skill is
  covered), or the overall Profile Match score is high.
- APPLY_STRETCH: real gaps remain, but the overall fit is still
  meaningfully positive - worth applying anyway.
- PREPARE_THEN_APPLY: a real, closeable gap - the kind of case Career
  Fit & Growth's project/course recommendations exist for.
- LOW_PRIORITY: weak overall fit. Still shown, still applyable - this
  is about return on the user's effort, not eligibility.
- EXCLUDE: reserved for a near-zero composite score only - i.e.
  almost nothing about the posting (title, location, skills,
  seniority) matched anything in the profile. This is deliberately
  NOT triggered by "requires more years of experience than the user
  has" alone, since a lopsided single signal like that can still leave
  title/location/skills matching - the product spec is explicit that
  years-of-experience alone must never exclude a job outright.

None of these tiers are a probability of an interview or an offer -
same disclosure the dashboard's Profile Match legend and Career Fit &
Growth's Requirement Coverage paragraph already carry.
"""

APPLY_NOW = "apply_now"
APPLY_STRETCH = "apply_stretch"
PREPARE_THEN_APPLY = "prepare_then_apply"
LOW_PRIORITY = "low_priority"
EXCLUDE = "exclude"

_LABELS = {
    APPLY_NOW: "Apply now",
    APPLY_STRETCH: "Apply - stretch",
    PREPARE_THEN_APPLY: "Prepare, then apply",
    LOW_PRIORITY: "Low priority",
    EXCLUDE: "Likely not a fit",
}

# Cutoffs against the V2 composite Profile Match score (0-100), used
# only when a stronger signal (ready_to_apply) isn't available. Kept as
# named constants, not magic numbers, so the reasoning is legible and
# the thresholds can be tuned in one place.
_APPLY_NOW_SCORE = 70
_APPLY_STRETCH_SCORE = 50
_PREPARE_THEN_APPLY_SCORE = 25
_LOW_PRIORITY_SCORE = 10


def classify_application_readiness(
    match_score,
    ready_to_apply=None,
    missing_required_count=None,
):
    """
    ``match_score``: the dashboard's own V2 Profile Match score (0-100).
    ``ready_to_apply``: Career Fit & Growth's own stronger signal, when
    available (``analyze_skill_gap(...)["ready_to_apply"]``) - every
    detected required skill is covered. Overrides the score-based tiers
    when True, since it's a more specific, catalog-grounded signal than
    the composite score alone.
    ``missing_required_count``: when available, used only to keep the
    reason text specific ("X required skills still missing") - never to
    push a job into EXCLUDE by itself.

    Returns {"level", "label", "reason"}.
    """

    match_score = match_score if match_score is not None else 0

    if ready_to_apply:
        return {
            "level": APPLY_NOW,
            "label": _LABELS[APPLY_NOW],
            "reason": (
                "Every required skill this posting asks for is already "
                "covered in your profile."
            ),
        }

    gap_note = (
        f" ({missing_required_count} required skill"
        f"{'s' if missing_required_count != 1 else ''} still missing)"
        if missing_required_count
        else ""
    )

    if match_score >= _APPLY_NOW_SCORE:
        level = APPLY_NOW
        reason = f"Strong overall fit (Profile Match {round(match_score)}%)."

    elif match_score >= _APPLY_STRETCH_SCORE:
        level = APPLY_STRETCH
        reason = (
            f"Solid overall fit (Profile Match {round(match_score)}%)"
            f"{gap_note} - worth applying."
        )

    elif match_score >= _PREPARE_THEN_APPLY_SCORE:
        level = PREPARE_THEN_APPLY
        reason = (
            f"Partial fit (Profile Match {round(match_score)}%){gap_note} "
            "- a realistic gap to close before applying."
        )

    elif match_score >= _LOW_PRIORITY_SCORE:
        level = LOW_PRIORITY
        reason = (
            f"Weak overall fit (Profile Match {round(match_score)}%) - "
            "still worth a look, but a lower-return use of your time "
            "than your stronger matches."
        )

    else:
        level = EXCLUDE
        reason = (
            f"Almost nothing about this posting - title, location, "
            f"skills, or seniority - matched your profile "
            f"(Profile Match {round(match_score)}%)."
        )

    return {"level": level, "label": _LABELS[level], "reason": reason}
