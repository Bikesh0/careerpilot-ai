
from flask import Blueprint, render_template, redirect

from app.search.manager import SearchManager
from app.search.v2.factory import (
    create_v2_service,
    v2_enabled,
)
from app.ai.matcher import JobMatcher
from app.ai.profile_loader import ProfileLoader
from app.services.application_service import ApplicationService
from app.services.ai_document_service import AIDocumentService


# =========================================================
# Blueprint
# =========================================================

web = Blueprint("web", __name__)


# =========================================================
# Services
# =========================================================

manager = SearchManager()
matcher = JobMatcher()
profile_loader = ProfileLoader()
document_ai = AIDocumentService()


# =========================================================
# SEARCH HELPERS
# =========================================================

def _load_profile():
    """Load the current user profile safely."""

    try:
        return profile_loader.load()

    except Exception as error:
        print(
            f"Profile loading failed: {error}"
        )

        return {}


def _search_jobs(profile=None):
    """
    Search using V2 when enabled.

    V1 remains the fallback if V2 is disabled
    or encounters an error.
    """

    if v2_enabled():

        try:

            service = create_v2_service(
                profile=profile
            )

            ranked = service.search(
                limit=50
            )

            print(
                f"V2 search returned "
                f"{len(ranked)} ranked jobs"
            )

            jobs = [
                item.job
                for item in ranked
            ]

            # CanonicalJob has no "id" field, and the dashboard's
            # Generate/Cover Letter/Save actions link to
            # /generate/<id> etc., which resolve through
            # manager.get_job(id). Assign local ids the same way
            # SearchManager.search_jobs() does for V1 jobs, and
            # register the list so those routes can find them.
            for index, job in enumerate(jobs):
                job.id = index

            manager.latest_jobs = jobs

            return jobs

        except Exception as error:

            print(
                f"V2 search failed, "
                f"falling back to V1: {error}"
            )

    try:

        return manager.search_jobs()

    except Exception as error:

        print(
            f"V1 search failed: {error}"
        )

        return []


def _rank_jobs(jobs, profile):
    """
    Keep the existing presentation ranking layer.

    V2 provides improved ingestion and matching data,
    while the existing matcher continues to provide
    dashboard-compatible ranked job objects.
    """

    try:

        return matcher.rank_jobs(
            jobs,
            profile
        )

    except Exception as error:

        print(
            f"Job ranking failed: {error}"
        )

        return []


# =========================================================
# DASHBOARD
# =========================================================

@web.route("/")
def dashboard():

    service = ApplicationService()
    stats = service.statistics()

    # -----------------------------------------------------
    # Load profile first
    # -----------------------------------------------------

    profile = _load_profile()

    # -----------------------------------------------------
    # Load jobs
    # -----------------------------------------------------

    if v2_enabled():

        jobs = _search_jobs(
            profile=profile
        )

    elif not getattr(
        manager,
        "latest_jobs",
        None,
    ):

        print(
            "Dashboard: no cached jobs, "
            "searching..."
        )

        jobs = _search_jobs(
            profile=profile
        )

    else:

        jobs = manager.latest_jobs

    # -----------------------------------------------------
    # Rank jobs
    # -----------------------------------------------------

    ranked = _rank_jobs(
        jobs,
        profile,
    )

    # -----------------------------------------------------
    # Render dashboard
    # -----------------------------------------------------

    return render_template(
        "dashboard.html",
        jobs=ranked,
        stats=stats,
    )


# =========================================================
# SEARCH
# =========================================================

@web.route("/search")
def search():

    # -----------------------------------------------------
    # Load profile first so V2 can rank against it
    # -----------------------------------------------------

    profile = _load_profile()

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    jobs = _search_jobs(
        profile=profile
    )

    # -----------------------------------------------------
    # Presentation ranking
    # -----------------------------------------------------

    ranked = _rank_jobs(
        jobs,
        profile,
    )

    service = ApplicationService()
    stats = service.statistics()

    return render_template(
        "dashboard.html",
        jobs=ranked,
        stats=stats,
    )


# =========================================================
# RESUME
# =========================================================

@web.route("/generate/<int:job_id>")
def generate(job_id):

    job = manager.get_job(job_id)

    if job is None:

        return "Job not found.", 404

    profile = profile_loader.load()

    try:

        resume = document_ai.resume_builder.build(
            profile,
            job
        )

    except Exception as error:

        print(
            f"Resume generation failed: {error}"
        )

        return (
            "AI resume generation is unavailable right now "
            "(the local Ollama model did not respond). "
            "Please try again once Ollama is running.",
            503,
        )

    return render_template(
        "resume.html",
        profile=profile,
        resume=resume,
        job=job
    )


# =========================================================
# COVER LETTER
# =========================================================

@web.route("/coverletter/<int:job_id>")
def coverletter(job_id):

    job = manager.get_job(job_id)

    if job is None:

        return "Job not found.", 404

    profile = profile_loader.load()

    try:

        letter = document_ai.cover_builder.build(
            profile,
            job
        )

    except Exception as error:

        print(
            f"Cover letter generation failed: {error}"
        )

        return (
            "AI cover letter generation is unavailable right now "
            "(the local Ollama model did not respond). "
            "Please try again once Ollama is running.",
            503,
        )

    return render_template(
        "coverletter.html",
        profile=profile,
        job=job,
        letter=letter
    )


# =========================================================
# SAVE JOB
# =========================================================

@web.route("/save/<int:job_id>")
def save_job(job_id):

    job = manager.get_job(job_id)

    if job is None:

        return "Job not found.", 404

    service = ApplicationService()

    service.save_job(job)

    return redirect("/")


# =========================================================
# APPLICATIONS
# =========================================================

@web.route("/applications")
def applications():

    service = ApplicationService()

    return render_template(
        "applications.html",
        applications=service.get_all()
    )


# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================

@web.route("/status/<int:app_id>/<status>")
def update_status(app_id, status):

    service = ApplicationService()

    service.update_status(
        app_id,
        status
    )

    return redirect("/applications")


# =========================================================
# DELETE APPLICATION
# =========================================================

@web.route("/delete/<int:app_id>")
def delete_application(app_id):

    service = ApplicationService()

    service.delete(app_id)

    return redirect("/applications")

