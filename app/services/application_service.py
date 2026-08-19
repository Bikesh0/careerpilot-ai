from datetime import datetime

from app.database.application_tracker import ApplicationTracker
from app.database.models import Application


# Statuses beyond "Interview" that still represent real, positive
# progress through the interview process - see _funnel_insight() and
# docs/PRODUCT_VISION.md's "Progressive employability" section. A
# rejection after reaching one of these does not erase that progress.
INTERVIEW_STAGE_STATUSES = ("Interview", "Second Round", "Final Round", "Offer")


def _funnel_insight(applied, interview_stage_or_later, offer):
    """
    One calm, honest observation about where the user's application
    funnel currently stands - never a checklist, never pressure.

    Deliberately requires a minimum sample size before suggesting a
    direction change, so a handful of early applications doesn't
    produce a false "your CV is weak" signal from pure noise.
    """

    if offer > 0:
        return (
            "You've received an offer - congratulations. Everything "
            "else here is secondary to that."
        )

    if applied < 5:
        return (
            "Not enough applications yet to spot a pattern - keep going."
        )

    interview_rate = interview_stage_or_later / applied

    if interview_stage_or_later >= 3:
        offer_rate = offer / interview_stage_or_later

        if offer_rate < 0.34:
            return (
                "You're reaching interviews consistently - the most "
                "useful focus now is interview preparation, not more "
                "applications or skill-building."
            )

    if interview_rate < 0.10:
        return (
            "Applications are going out but interviews are rare so "
            "far - it may help to strengthen your CV evidence or focus "
            "on more closely-matched jobs before applying to more."
        )

    return (
        "Your application funnel looks healthy so far - keep applying "
        "to well-matched roles."
    )


class ApplicationService:

    def __init__(self):

        self.tracker = ApplicationTracker()

    def save_job(self, job):

        application = Application(

    company=job.company,

    title=job.title,

    location=job.location,

    source=job.source,

    status="Saved",

    applied_date=datetime.now().strftime("%Y-%m-%d"),

    job_url=job.url

)

        self.tracker.save(application)

    def get_all(self):

        return self.tracker.get_all()

    def update_status(self, app_id, status):

        self.tracker.update_status(app_id, status)

    def delete(self, app_id):

        self.tracker.delete(app_id)

    def status_for_job_url(self, job_url):
        """
        Current status for a job, by URL, or None if no application has
        ever been saved for it. Used to gate interview preparation -
        see app/web/routes.py's interview_prep() and
        INTERVIEW_STAGE_STATUSES above.
        """

        return self.tracker.get_status_by_job_url(job_url)

    # =====================
    # Dashboard Statistics
    # =====================

    def statistics(self):

        applied = self.tracker.count_status("Applied")
        interview = self.tracker.count_status("Interview")
        second_round = self.tracker.count_status("Second Round")
        final_round = self.tracker.count_status("Final Round")
        offer = self.tracker.count_status("Offer")

        # Real progress through the funnel, not just the exact
        # "Interview" status - a candidate in "Second Round" or "Final
        # Round" has demonstrably progressed further than "Interview"
        # alone would suggest. See INTERVIEW_STAGE_STATUSES.
        interview_stage_or_later = (
            interview + second_round + final_round + offer
        )

        return {

            "applications": self.tracker.count_all(),

            "saved": self.tracker.count_status("Saved"),

            "applied": applied,

            "interview": interview,

            "second_round": second_round,

            "final_round": final_round,

            "offer": offer,

            "rejected": self.tracker.count_status("Rejected"),

            "no_response": self.tracker.count_status("No Response"),

            "withdrawn": self.tracker.count_status("Withdrawn"),

            "interview_stage_or_later": interview_stage_or_later,

            "insight": _funnel_insight(
                applied, interview_stage_or_later, offer
            ),

        }