from flask import Blueprint, render_template, redirect

from app.search.manager import SearchManager
from app.ai.matcher import JobMatcher
from app.ai.profile_loader import ProfileLoader
from app.services.application_service import ApplicationService
from app.services.ai_document_service import AIDocumentService


web = Blueprint("web", __name__)

manager = SearchManager()
matcher = JobMatcher()
profile_loader = ProfileLoader()
document_ai = AIDocumentService()


@web.route("/")
def dashboard():
    service = ApplicationService()
    stats = service.statistics()

    return render_template(
        "dashboard.html",
        jobs=None,
        stats=stats
    )


@web.route("/search")
def search():
    jobs = manager.search_jobs()

    profile = profile_loader.load()

    ranked = matcher.rank_jobs(
        jobs,
        profile
    )

    service = ApplicationService()
    stats = service.statistics()

    return render_template(
        "dashboard.html",
        jobs=ranked,
        stats=stats
    )


@web.route("/generate/<int:job_id>")
def generate(job_id):
    job = manager.get_job(job_id)

    if job is None:
        return "Job not found."

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


@web.route("/coverletter/<int:job_id>")
def coverletter(job_id):
    job = manager.get_job(job_id)

    if job is None:
        return "Job not found."

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


@web.route("/save/<int:job_id>")
def save_job(job_id):
    job = manager.get_job(job_id)

    if job is None:
        return "Job not found."

    service = ApplicationService()
    service.save_job(job)

    return redirect("/")


@web.route("/applications")
def applications():
    service = ApplicationService()

    return render_template(
        "applications.html",
        applications=service.get_all()
    )


@web.route("/status/<int:app_id>/<status>")
def update_status(app_id, status):
    service = ApplicationService()

    service.update_status(
        app_id,
        status
    )

    return redirect("/applications")


@web.route("/delete/<int:app_id>")
def delete_application(app_id):
    service = ApplicationService()

    service.delete(app_id)

    return redirect("/applications")