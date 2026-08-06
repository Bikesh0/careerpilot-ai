from flask import Blueprint
from flask import render_template
from flask import send_file

from flask import send_file
from app.services.document_service import DocumentService
from app.services.profile_service import ProfileService
from app.search.search_manager import SearchManager
from app.search.manager import SearchManager
from app.ai.matcher import JobMatcher
from app.ai.profile_loader import ProfileLoader
from app.ai.resume_generator import ResumeGenerator

web = Blueprint("web", __name__)

manager = SearchManager()
matcher = JobMatcher()
profile_loader = ProfileLoader()
resume_ai = ResumeGenerator()


@web.route("/")
def dashboard():

    return render_template(
        "dashboard.html",
        jobs=None
    )

@web.route("/generate/<int:job_id>")
def generate(job_id):

    manager = SearchManager()

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


@web.route("/search")
def search():

    jobs = manager.search_jobs()

    profile = profile_loader.load()

    ranked = matcher.rank_jobs(
        jobs,
        profile
    )

    return render_template(
        "dashboard.html",
        jobs=ranked
    )


@web.route("/resume/<int:job_id>")
def resume(job_id):

    job = manager.get_job(job_id)

    if job is None:
        return "Job not found"

    profile = profile_loader.load()

    filename = resume_ai.generate(
        job,
        profile
    )

    return send_file(
        filename,
        as_attachment=True
    )