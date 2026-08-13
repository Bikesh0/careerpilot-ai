from flask import Blueprint, render_template, redirect

from app.search.manager import SearchManager
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
# DASHBOARD
# =========================================================

@web.route("/")
def dashboard():

    service = ApplicationService()
    stats = service.statistics()

    # -----------------------------------------------------
    # Load jobs
    # -----------------------------------------------------

    if not getattr(manager, "latest_jobs", None):

        print("Dashboard: no cached jobs, searching...")

        try:

            jobs = manager.search_jobs()

        except Exception as error:

            print(
                f"Dashboard search failed: {error}"
            )

            jobs = []

    else:

        jobs = manager.latest_jobs

    # -----------------------------------------------------
    # Load profile
    # -----------------------------------------------------

    try:

        profile = profile_loader.load()

    except Exception as error:

        print(
            f"Dashboard profile loading failed: {error}"
        )

        profile = {}

    # -----------------------------------------------------
    # Rank jobs
    # -----------------------------------------------------

    try:

        ranked = matcher.rank_jobs(
            jobs,
            profile
        )

    except Exception as error:

        print(
            f"Dashboard ranking failed: {error}"
        )

        ranked = []

    # -----------------------------------------------------
    # Render dashboard
    # -----------------------------------------------------

    return render_template(
        "dashboard.html",
        jobs=ranked,
        stats=stats
    )


# =========================================================
# SEARCH
# =========================================================

@web.route("/search")
def search():

    try:

        jobs = manager.search_jobs()

    except Exception as error:

        print(
            f"Search failed: {error}"
        )

        jobs = []

    try:

        profile = profile_loader.load()

    except Exception as error:

        print(
            f"Profile loading failed: {error}"
        )

        profile = {}

    try:

        ranked = matcher.rank_jobs(
            jobs,
            profile
        )

    except Exception as error:

        print(
            f"Search ranking failed: {error}"
        )

        ranked = []

    service = ApplicationService()
    stats = service.statistics()

    return render_template(
        "dashboard.html",
        jobs=ranked,
        stats=stats
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

    resume = document_ai.resume_builder.build(
        profile,
        job
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

    letter = document_ai.cover_builder.build(
        profile,
        job
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