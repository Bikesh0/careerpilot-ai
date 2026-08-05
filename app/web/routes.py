from flask import Blueprint, render_template

from app.search.manager import SearchManager
from app.ai.matcher import JobMatcher

web = Blueprint("web", __name__)


@web.route("/")
def dashboard():

    manager = SearchManager()

    matcher = JobMatcher()

    jobs = manager.search_jobs()

    profile = {
        "skills": [
            "Linux",
            "Python",
            "Splunk",
            "Docker",
            "Azure",
            "Networking",
            "Cyber Security"
        ]
    }

    ranked = matcher.rank_jobs(
        jobs,
        profile
    )

    return render_template(
        "dashboard.html",
        jobs=ranked[:10]
    )