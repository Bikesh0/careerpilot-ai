
import time
import uuid
from collections import defaultdict
from pathlib import Path

from flask import Blueprint, render_template, redirect, request

from app.search.manager import SearchManager
from app.search.v2.factory import (
    create_v2_service,
    v2_enabled,
)
from app.ai.matcher import JobMatcher
from app.ai.profile_loader import ProfileLoader
from app.ai.profile_extractor import ProfileExtractor
from app.ai.skill_gap import analyze_skill_gap, SKILL_CATALOG
from app.ai.geo_normalizer import is_excluded_by_default
from app.ai.cv_strength import analyze_cv_strength
from app.ai.interview_prep import InterviewPrepBuilder
from app.ai.project_coach import ProjectCoach
from app.parsers.cv_parser import CVParser
from app.services.application_service import (
    ApplicationService,
    INTERVIEW_STAGE_STATUSES,
)
from app.services.project_service import ProjectService
from app.database.project_tracker import PROJECT_STATUSES
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
profile_extractor = ProfileExtractor()
cv_parser = CVParser()
interview_prep_builder = InterviewPrepBuilder()
project_coach = ProjectCoach()


# =========================================================
# CV upload
# =========================================================

CV_UPLOAD_DIR = Path("data") / "cv_uploads"

ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}


def _save_uploaded_cv(uploaded_file):
    """
    Save an uploaded CV to a project-controlled path.

    The client-supplied filename is never used to build the
    destination path - only its extension is trusted, and only after
    checking it against an allow-list. The actual filename on disk is
    a fresh UUID, which also rules out overwriting another user's
    upload via a repeated/predictable name.
    """

    suffix = Path(uploaded_file.filename or "").suffix.lower()

    if suffix not in ALLOWED_CV_EXTENSIONS:
        raise ValueError(
            "Only PDF and DOCX files are supported."
        )

    CV_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = CV_UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    uploaded_file.save(destination)

    return destination


# CV data is personal data - minimize retention (see docs/SECURITY.md).
# Every upload attempt does a best-effort sweep for files past this
# window before saving the new one; a real background scheduler would
# be overbuilt for a "few users/day" beta demo.
CV_UPLOAD_RETENTION_SECONDS = 24 * 60 * 60


def _cleanup_old_uploads():
    if not CV_UPLOAD_DIR.exists():
        return

    cutoff = time.time() - CV_UPLOAD_RETENTION_SECONDS

    for path in CV_UPLOAD_DIR.iterdir():
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            # Cleanup is best-effort and must never break an upload.
            continue


# Lightweight, dependency-free rate limiting for the one route that
# accepts a file upload and calls an AI model - relevant mainly if this
# is ever exposed via a tunnel to more than the owner (see
# docs/SECURITY.md's "Exposing this app to testers" section). Deliberately
# in-memory, not persisted - resets on restart, which is an accepted
# tradeoff for a small local/beta tool, not a production rate limiter.
_UPLOAD_ATTEMPTS = defaultdict(list)
UPLOAD_RATE_LIMIT = 20
UPLOAD_RATE_WINDOW_SECONDS = 60


def _upload_rate_limited(remote_addr):
    now = time.time()
    attempts = _UPLOAD_ATTEMPTS[remote_addr or "unknown"]
    attempts[:] = [
        seen for seen in attempts if now - seen < UPLOAD_RATE_WINDOW_SECONDS
    ]

    if len(attempts) >= UPLOAD_RATE_LIMIT:
        return True

    attempts.append(now)
    return False


def _reset_upload_rate_limit():
    """Test-only helper - clears shared rate-limit state between tests."""

    _UPLOAD_ATTEMPTS.clear()


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


# The dashboard route ("/") used to call _search_jobs() unconditionally
# on every single load whenever V2 is enabled, with no caching at all -
# meaning every visit re-ran the full multi-source search from scratch,
# including Jobly's mandatory 10-second-per-request crawl-delay pause
# (see docs/DATA_SOURCES.md). For ~15-20 Jobly postings that's 2-3
# minutes, every time, even for a page load seconds after the last one.
# This cache makes repeat dashboard visits within the TTL reuse the same
# results instead of re-searching - it changes nothing about how a
# search is performed or how jobs are matched/ranked once one actually
# runs. The explicit "Search Jobs" action (/search) always bypasses this
# and forces a fresh search, since that's the whole point of clicking it.
_V2_SEARCH_CACHE_TTL_SECONDS = 300

_v2_search_cache = {
    "jobs": None,
    "fetched_at": 0.0,
    "service_factory": None,
}


def _search_jobs(profile=None, force_refresh=False):
    """
    Search using V2 when enabled.

    V1 remains the fallback if V2 is disabled
    or encounters an error.
    """

    if v2_enabled():

        cache_age = time.time() - _v2_search_cache["fetched_at"]

        # Also invalidated if create_v2_service itself has changed
        # since the cache was filled - in production this reference
        # never changes between requests, so this has no effect beyond
        # the TTL. It matters for tests, which monkeypatch
        # create_v2_service to a fresh fake per test: without this
        # check, one test's cached jobs would leak into the next.
        cache_is_fresh = (
            _v2_search_cache["jobs"] is not None
            and cache_age < _V2_SEARCH_CACHE_TTL_SECONDS
            and _v2_search_cache["service_factory"] is create_v2_service
        )

        if cache_is_fresh and not force_refresh:

            print(
                f"V2 search: reusing cached results "
                f"({round(cache_age)}s old)"
            )

            manager.latest_jobs = _v2_search_cache["jobs"]

            return _v2_search_cache["jobs"]

        try:

            service = create_v2_service(
                profile=profile
            )

            ranked = service.search(
                limit=50
            )

            # Geographic scope: Finland first, Europe second, outside
            # Europe excluded by default (see app/ai/geo_normalizer.py
            # - a location it can't confidently classify is never
            # excluded, only a confidently-identified non-European one
            # is). Filtered here, before local ids are assigned below,
            # so /analyze/<id> etc. always resolve to the same job the
            # dashboard actually displays at that position.
            ranked = [
                item for item in ranked
                if not is_excluded_by_default(
                    getattr(item.job, "location", "")
                )
            ]

            print(
                f"V2 search returned "
                f"{len(ranked)} ranked jobs"
            )

            jobs = []

            for index, item in enumerate(ranked):

                # CanonicalJob has no "id" field, and the dashboard's
                # Generate/Cover Letter/Save actions link to
                # /generate/<id> etc., which resolve through
                # manager.get_job(id). Assign local ids the same way
                # SearchManager.search_jobs() does for V1 jobs.
                item.job.id = index

                # Stash the MatchResult V2's own JobRanker already
                # computed for this job, so _rank_jobs() can reuse it
                # directly instead of re-scoring through the legacy
                # matcher. This is what lets V2 own presentation-layer
                # scoring end to end when it's the actual source of
                # the job list - see _rank_jobs().
                item.job._v2_match = item.match

                jobs.append(item.job)

            manager.latest_jobs = jobs

            _v2_search_cache["jobs"] = jobs
            _v2_search_cache["fetched_at"] = time.time()
            _v2_search_cache["service_factory"] = create_v2_service

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
    Build the dashboard's ranked job list.

    Ownership is decided by where the job data actually came from,
    not by re-checking the feature flag: jobs collected via the V2
    pipeline carry the MatchResult V2's own JobRanker already computed
    (stashed onto each CanonicalJob by _search_jobs as `_v2_match`).
    When every job in the list carries one, V2 owns scoring - its
    score/matched_skills/reasons are reused directly, in the order V2
    already ranked them, with no second pass through the legacy
    matcher.

    Jobs with no stashed match - V1 Job objects from the fallback path
    when V2 is disabled, or when V2 search/ranking itself failed and
    _search_jobs() fell back to manager.search_jobs() - go through the
    existing legacy JobMatcher exactly as before. Legacy behavior is
    completely unchanged whenever V2 isn't the actual source of the
    job list.
    """

    if jobs and all(
        getattr(job, "_v2_match", None) is not None
        for job in jobs
    ):

        try:

            return _present_v2_ranked_jobs(jobs)

        except Exception as error:

            print(
                f"V2 result presentation failed, "
                f"falling back to legacy matcher: {error}"
            )

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


def _present_v2_ranked_jobs(jobs):
    """
    Adapt V2's own match results into the dashboard's presentation
    shape (the same {"job": ..., "match_score": ..., "matched_skills":
    ...} shape the legacy matcher already produces), without
    re-scoring or re-sorting - `jobs` is already in V2's ranked order.
    """

    presented = []

    for job in jobs:

        match = job._v2_match

        job_dict = job.to_dict()
        job_dict["id"] = job.id

        presented.append(
            {
                "job": job_dict,
                "match_score": round(match.score),
                "matched_skills": match.matched_skills,
                "missing_skills": match.missing_skills,
                "match_reasons": match.reasons,
            }
        )

    return presented


def _attach_interview_readiness(ranked):
    """
    Flag each ranked job with whether interview preparation should be
    offered for it - only once a saved application for that exact job
    (matched by URL) has reached "Interview" status or later. See
    INTERVIEW_STAGE_STATUSES and the /interview/<job_id> route.

    Deliberately gated here (once, for the whole list) rather than
    inside the template, so the gating logic lives in one place.
    """

    service = ApplicationService()

    for item in ranked:

        job = item.get("job")

        job_url = (
            job.get("url", "")
            if isinstance(job, dict)
            else getattr(job, "url", "")
        )

        status = (
            service.status_for_job_url(job_url)
            if job_url else None
        )

        item["interview_ready"] = status in INTERVIEW_STAGE_STATUSES

    return ranked


# =========================================================
# CV STRENGTH (Layer 1 - general, job-independent analysis)
# =========================================================

@web.route("/cv-strength")
def cv_strength():

    profile = _load_profile()

    verified_skill_keys = ProjectService().verified_skill_keys()

    analysis = analyze_cv_strength(profile, verified_skill_keys)

    return render_template(
        "cv_strength.html",
        profile=profile,
        analysis=analysis,
    )


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

    ranked = _attach_interview_readiness(ranked)

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
    # Search - always fresh: this is the explicit "Search Jobs"
    # action, so it must bypass the dashboard's cache rather than
    # silently reuse old results.
    # -----------------------------------------------------

    jobs = _search_jobs(
        profile=profile,
        force_refresh=True,
    )

    # -----------------------------------------------------
    # Presentation ranking
    # -----------------------------------------------------

    ranked = _rank_jobs(
        jobs,
        profile,
    )

    ranked = _attach_interview_readiness(ranked)

    service = ApplicationService()
    stats = service.statistics()

    return render_template(
        "dashboard.html",
        jobs=ranked,
        stats=stats,
    )


# =========================================================
# SIDEBAR LANDING PAGES
#
# The sidebar (templates/base.html) links to /resume,
# /coverletter, /interview, and /settings. None of these
# routes existed, so every one of those links 404'd.
#
# Resume/cover-letter generation is inherently job-specific
# (/generate/<id>, /coverletter/<id>), so a bare /resume or
# /coverletter visit sends the user to the dashboard, where
# they can pick a job. /settings renders its existing page.
# =========================================================

@web.route("/resume")
def resume_landing():

    return redirect("/")


@web.route("/coverletter")
def coverletter_landing():

    return redirect("/")


# =========================================================
# INTERVIEW PREPARATION
#
# Deliberately gated: proactively generating interview prep for a job
# the user hasn't reached interview stage for would work against the
# product's "calm advisor, not pressure" principle (see
# docs/PRODUCT_VISION.md). The bare /interview landing explains the
# gate; /interview/<job_id> is the real, job-specific, AI-generated
# page, only reachable once that job's saved application status is
# "Interview" or later.
# =========================================================

@web.route("/interview")
def interview():

    return render_template(
        "interview.html",
        job=None,
    )


@web.route("/interview/<int:job_id>")
def interview_prep(job_id):

    job = manager.get_job(job_id)

    if job is None:

        return "Job not found.", 404

    service = ApplicationService()

    status = service.status_for_job_url(
        getattr(job, "url", "")
    )

    if status not in INTERVIEW_STAGE_STATUSES:

        return render_template(
            "interview.html",
            job=job,
            gated=True,
            status=status,
        )

    profile = _load_profile()

    skill_analysis = analyze_skill_gap(profile, job)

    missing_skills = [
        entry["skill"]
        for entry in skill_analysis.get("required", [])
        if entry["status"] == "missing"
    ]

    try:

        questions = interview_prep_builder.build(
            profile,
            job,
            missing_skills=missing_skills,
        )

    except Exception as error:

        print(
            f"Interview prep generation failed: {error}"
        )

        return (
            "AI interview preparation is unavailable right now "
            "(the local Ollama model did not respond). "
            "Please try again once Ollama is running.",
            503,
        )

    return render_template(
        "interview.html",
        job=job,
        gated=False,
        status=status,
        questions=questions,
    )


@web.route("/settings")
def settings():

    return render_template(
        "settings.html",
        extracted=None,
        upload_error=None,
    )


@web.route("/settings/upload-cv", methods=["POST"])
def upload_cv():

    _cleanup_old_uploads()

    if _upload_rate_limited(request.remote_addr):

        return render_template(
            "settings.html",
            extracted=None,
            upload_error=(
                "Too many upload attempts - please wait a minute and "
                "try again."
            ),
        ), 429

    uploaded_file = request.files.get("cv_file")

    if uploaded_file is None or not uploaded_file.filename:

        return render_template(
            "settings.html",
            extracted=None,
            upload_error="Please choose a PDF or DOCX file.",
        )

    try:

        saved_path = _save_uploaded_cv(uploaded_file)

    except ValueError as error:

        return render_template(
            "settings.html",
            extracted=None,
            upload_error=str(error),
        )

    try:

        cv_text = cv_parser.parse(saved_path)

    except Exception as error:

        print(
            f"CV parsing failed: {error}"
        )

        return render_template(
            "settings.html",
            extracted=None,
            upload_error=(
                "Could not read that file. Make sure it is a valid "
                "PDF or DOCX CV."
            ),
        )

    try:

        extracted = profile_extractor.extract(cv_text)

    except Exception as error:

        print(
            f"CV profile extraction failed: {error}"
        )

        return render_template(
            "settings.html",
            extracted=None,
            upload_error=(
                "AI extraction is unavailable right now (the local "
                "Ollama model did not respond). The file was saved; "
                "please try again once Ollama is running."
            ),
        )

    return render_template(
        "settings.html",
        extracted=extracted,
        upload_error=None,
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
# SKILL GAP ANALYSIS
# =========================================================

@web.route("/analyze/<int:job_id>")
def analyze(job_id):

    job = manager.get_job(job_id)

    if job is None:

        return "Job not found.", 404

    profile = _load_profile()

    analysis = analyze_skill_gap(
        profile,
        job,
        existing_projects=ProjectService().get_all(),
    )

    return render_template(
        "skill_gap.html",
        job=job,
        analysis=analysis,
    )


# =========================================================
# PROJECTS - the AI-coached "close the gap" action
#
# Turns a skill-gap recommendation into a real, tracked project:
# Planned -> In Progress -> Completed -> Verified. Status only ever
# changes via an explicit user action (never automatically - see
# docs/PRODUCT_VISION.md). A CV bullet can only be drafted once a
# project is Verified, and is always review-only - nothing here writes
# to profiles/profile.json.
# =========================================================

def _start_project_from_catalog(skill_key, source_job_url=""):
    """
    Shared by both "start a project" entry points - a job-specific gap
    (Layer 2, /analyze/<job_id>) and a general CV-strength weakness
    (Layer 1, /cv-strength), which has no job context at all. Returns
    the new project's id, or None if skill_key isn't a real catalog key.
    """

    entry = SKILL_CATALOG.get(skill_key)

    if entry is None:
        return None

    catalog_projects = entry.get("projects") or []

    if catalog_projects:
        title = catalog_projects[0]["title"]
        description = catalog_projects[0]["description"]
    else:
        title = f"{entry['display']} practical project"
        description = (
            f"Build hands-on, demonstrable evidence of {entry['display']}."
        )

    service = ProjectService()

    return service.start_project(
        skill_key=skill_key,
        skill_display=entry["display"],
        title=title,
        description=description,
        source_job_url=source_job_url,
    )


@web.route("/projects/start/<int:job_id>/<skill_key>")
def start_project(job_id, skill_key):

    job = manager.get_job(job_id)

    source_job_url = getattr(job, "url", "") if job is not None else ""

    project_id = _start_project_from_catalog(skill_key, source_job_url)

    if project_id is None:

        return "Unknown skill.", 404

    return redirect(f"/projects/{project_id}")


@web.route("/projects/start-general/<skill_key>")
def start_project_general(skill_key):
    """
    Same as start_project(), but for a project started from the
    job-independent Layer 1 CV-strength page - no job to attribute it
    to.
    """

    project_id = _start_project_from_catalog(skill_key)

    if project_id is None:

        return "Unknown skill.", 404

    return redirect(f"/projects/{project_id}")


@web.route("/projects")
def projects():

    service = ProjectService()

    return render_template(
        "projects.html",
        projects=service.get_all(),
        stats=service.statistics(),
    )


@web.route("/projects/<int:project_id>")
def project_detail(project_id):

    service = ProjectService()

    project = service.get(project_id)

    if project is None:

        return "Project not found.", 404

    return render_template(
        "project_detail.html",
        project=project,
        statuses=PROJECT_STATUSES,
        coach_error=None,
    )


@web.route("/projects/<int:project_id>/status/<status>")
def update_project_status(project_id, status):

    service = ProjectService()

    if service.get(project_id) is None:

        return "Project not found.", 404

    try:

        service.update_status(project_id, status)

    except ValueError as error:

        return str(error), 400

    return redirect(f"/projects/{project_id}")


@web.route("/projects/<int:project_id>/ask", methods=["POST"])
def ask_project_coach(project_id):

    service = ProjectService()

    project = service.get(project_id)

    if project is None:

        return "Project not found.", 404

    question = (request.form.get("question") or "").strip()

    if not question:

        return redirect(f"/projects/{project_id}")

    try:

        answer = project_coach.ask(project, question)

        service.append_note(
            project_id,
            f"Q: {question}\nA (AI coach): {answer}",
        )

    except Exception as error:

        print(
            f"Project coach failed: {error}"
        )

        return render_template(
            "project_detail.html",
            project=project,
            statuses=PROJECT_STATUSES,
            coach_error=(
                "AI project coaching is unavailable right now (the "
                "local Ollama model did not respond). Please try again "
                "once Ollama is running."
            ),
        )

    return redirect(f"/projects/{project_id}")


@web.route("/projects/<int:project_id>/plan")
def get_project_plan(project_id):

    service = ProjectService()

    project = service.get(project_id)

    if project is None:

        return "Project not found.", 404

    try:

        plan = project_coach.plan(project)

        service.append_note(
            project_id,
            f"Step-by-step plan:\n{plan}",
        )

    except Exception as error:

        print(
            f"Project coach plan generation failed: {error}"
        )

        return render_template(
            "project_detail.html",
            project=project,
            statuses=PROJECT_STATUSES,
            coach_error=(
                "AI project coaching is unavailable right now (the "
                "local Ollama model did not respond). Please try again "
                "once Ollama is running."
            ),
        )

    return redirect(f"/projects/{project_id}")


@web.route("/projects/<int:project_id>/review", methods=["POST"])
def review_project_work(project_id):

    service = ProjectService()

    project = service.get(project_id)

    if project is None:

        return "Project not found.", 404

    submission = (request.form.get("submission") or "").strip()

    if not submission:

        return redirect(f"/projects/{project_id}")

    try:

        feedback = project_coach.review(project, submission)

        service.append_note(
            project_id,
            f"Submitted for review:\n{submission}\n\n"
            f"AI coach feedback:\n{feedback}",
        )

    except Exception as error:

        print(
            f"Project coach review failed: {error}"
        )

        return render_template(
            "project_detail.html",
            project=project,
            statuses=PROJECT_STATUSES,
            coach_error=(
                "AI project coaching is unavailable right now (the "
                "local Ollama model did not respond). Please try again "
                "once Ollama is running."
            ),
        )

    return redirect(f"/projects/{project_id}")


@web.route("/projects/<int:project_id>/cv-bullet")
def draft_project_cv_bullet(project_id):

    service = ProjectService()

    project = service.get(project_id)

    if project is None:

        return "Project not found.", 404

    if project["status"] != "Verified":

        return (
            "A CV bullet can only be drafted for a Verified project - "
            "mark this project Verified once the real evidence "
            "(repo, README, findings) actually exists.",
            400,
        )

    try:

        bullet = project_coach.draft_cv_bullet(project)

        service.set_cv_bullet(project_id, bullet)

    except Exception as error:

        print(
            f"CV-bullet drafting failed: {error}"
        )

        return (
            "AI CV-bullet drafting is unavailable right now (the local "
            "Ollama model did not respond). Please try again once "
            "Ollama is running.",
            503,
        )

    return redirect(f"/projects/{project_id}")


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
        applications=service.get_all(),
        stats=service.statistics(),
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

