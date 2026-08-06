from flask import Blueprint
from flask import render_template
from flask import send_file
from flask import redirect

from app.search.manager import SearchManager
from app.ai.matcher import JobMatcher
from app.ai.profile_loader import ProfileLoader
from app.ai.resume_generator import ResumeGenerator

from app.services.application_service import ApplicationService
from app.services.document_service import DocumentService
from app.services.profile_service import ProfileService

web = Blueprint("web", __name__)

manager = SearchManager()
matcher = JobMatcher()
profile_loader = ProfileLoader()
resume_ai = ResumeGenerator()


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


@web.route("/resume/<int:job_id>")
def resume(job_id):

    job = manager.get_job(job_id)

    if job is None:
        return "Job not found."

    profile = profile_loader.load()

    filename = resume_ai.generate(
        job,
        profile
    )

    return send_file(
        filename,
        as_attachment=True
    )


@web.route("/generate/<int:job_id>")
def generate(job_id):

    job = manager.get_job(job_id)

    if job is None:
        return "Job not found."

    profile = ProfileService()

    cv_path = profile.get_master_cv()

    document = DocumentService()

    filename = document.generate_resume(
        cv_path,
        job
    )

    return send_file(
        filename,
        as_attachment=True
    )


@web.route("/coverletter/<int:job_id>")
def coverletter(job_id):

    job = manager.get_job(job_id)

    if job is None:
        return "Job not found."

    profile = ProfileService()

    cv_path = profile.get_master_cv()

    document = DocumentService()

    filename = document.generate_cover_letter(
        cv_path,
        job
    )

    return send_file(
        filename,
        as_attachment=True
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