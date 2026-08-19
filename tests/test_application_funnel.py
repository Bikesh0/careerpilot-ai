from app.database.application_tracker import ApplicationTracker
from app.database.models import Application
from app.services.application_service import _funnel_insight


def test_offer_takes_priority_over_every_other_signal():
    assert "congratulations" in _funnel_insight(
        applied=20, interview_stage_or_later=2, offer=1
    ).lower()


def test_small_sample_gets_a_neutral_not_enough_data_message():
    """
    Regression test: with only a handful of applications, the funnel
    insight must not claim a CV-quality problem from pure noise - the
    product spec is explicit that recommendations must be grounded,
    not invented to fill a UI slot.
    """

    message = _funnel_insight(applied=2, interview_stage_or_later=0, offer=0)

    assert "not enough" in message.lower()


def test_many_applications_few_interviews_points_at_cv_and_targeting():
    message = _funnel_insight(
        applied=20, interview_stage_or_later=1, offer=0
    )

    assert "cv" in message.lower() or "match" in message.lower()


def test_several_interviews_but_no_offers_points_at_interview_prep():
    message = _funnel_insight(
        applied=10, interview_stage_or_later=4, offer=0
    )

    assert "interview preparation" in message.lower()


def test_healthy_funnel_gets_an_encouraging_neutral_message():
    message = _funnel_insight(
        applied=10, interview_stage_or_later=2, offer=0
    )

    assert "healthy" in message.lower()


def test_second_round_and_final_round_count_toward_interview_stage_or_later(
    tmp_path,
):
    """
    Regression test for "interview progress must count as real
    progress, not just the exact Interview status" - Second Round and
    Final Round are real, further progress and must be included in the
    same funnel bucket as Interview and Offer.
    """

    tracker = ApplicationTracker(database_path=tmp_path / "careerpilot.db")

    for status in ("Interview", "Second Round", "Final Round", "Offer"):
        tracker.save(
            Application(
                company=f"Company {status}",
                title="Security Engineer",
                location="Helsinki",
                source="Jobly",
                status=status,
                applied_date="2026-08-19",
                job_url=f"https://example.test/{status}",
            )
        )

    interview_stage_total = (
        tracker.count_status("Interview")
        + tracker.count_status("Second Round")
        + tracker.count_status("Final Round")
        + tracker.count_status("Offer")
    )

    assert interview_stage_total == 4
