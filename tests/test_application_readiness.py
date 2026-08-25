from app.ai.application_readiness import (
    APPLY_NOW,
    APPLY_STRETCH,
    EXCLUDE,
    LOW_PRIORITY,
    PREPARE_THEN_APPLY,
    classify_application_readiness,
)


def test_ready_to_apply_signal_overrides_the_score():
    result = classify_application_readiness(
        match_score=40, ready_to_apply=True
    )

    assert result["level"] == APPLY_NOW


def test_high_score_without_ready_to_apply_is_apply_now():
    result = classify_application_readiness(match_score=75)

    assert result["level"] == APPLY_NOW


def test_mid_score_is_apply_stretch():
    result = classify_application_readiness(match_score=55)

    assert result["level"] == APPLY_STRETCH


def test_lower_score_is_prepare_then_apply():
    result = classify_application_readiness(match_score=30)

    assert result["level"] == PREPARE_THEN_APPLY


def test_weak_score_is_low_priority_not_excluded():
    """
    Regression test for the product spec's explicit rule: a weak but
    non-trivial score must never be auto-excluded, only deprioritized.
    """

    result = classify_application_readiness(match_score=12)

    assert result["level"] == LOW_PRIORITY


def test_near_zero_score_is_excluded():
    result = classify_application_readiness(match_score=3)

    assert result["level"] == EXCLUDE


def test_missing_required_count_is_reflected_in_the_reason_text():
    result = classify_application_readiness(
        match_score=55, missing_required_count=2
    )

    assert "2 required skills" in result["reason"]


def test_none_match_score_does_not_crash_and_is_treated_as_weakest():
    result = classify_application_readiness(match_score=None)

    assert result["level"] == EXCLUDE
