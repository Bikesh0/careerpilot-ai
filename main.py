import json
import os

from app.search.manager import SearchManager
from app.search.filter import JobFilter
from app.search.job_memory import JobMemory

from app.ai.matcher import JobMatcher
from app.ai.analyzer import JobAnalyzer
from app.ai.decision import DecisionEngine
from app.ai.prioritizer import JobPrioritizer
from app.ai.job_intelligence import JobIntelligence
from app.ai.application import ApplicationAssistant

from app.database.database import (
    initialize_database,
    get_connection,
    job_exists,
)

from app.database.application_tracker import (
    ApplicationTracker,
)


# =============================================================
# Configuration
# =============================================================

MAX_AI_ANALYSIS = 5


# =============================================================
# Profile
# =============================================================

def load_profile():

    with open(
        "profiles/profile.json",
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =============================================================
# Report
# =============================================================

def save_report(data):

    os.makedirs(
        "output",
        exist_ok=True,
    )

    with open(
        "output/jobs_report.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =============================================================
# Database
# =============================================================

def save_jobs_to_database(results):

    conn = get_connection()

    cursor = conn.cursor()

    saved = 0

    for job in results:

        try:

            if job_exists(
                job["job_title"],
                job["company"],
            ):

                continue

            decision = job.get(
                "decision",
                {},
            )

            decision_value = decision.get(
                "decision",
                "CONSIDER APPLYING",
            )

            cursor.execute(
                """
                INSERT INTO jobs
                (
                    title,
                    company,
                    location,
                    description,
                    source,
                    url,
                    match_score,
                    decision
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job["job_title"],
                    job.get(
                        "company",
                        "",
                    ),
                    job.get(
                        "location",
                        "",
                    ),
                    job.get(
                        "description",
                        "",
                    ),
                    job.get(
                        "source",
                        "",
                    ),
                    job.get(
                        "url",
                        "",
                    ),
                    job.get(
                        "match_score",
                        0,
                    ),
                    decision_value,
                ),
            )

            saved += 1

        except Exception as error:

            print(
                "⚠️ Database save failed:",
                error,
            )

            continue

    conn.commit()

    conn.close()

    print(
        f"Saved {saved} jobs."
    )


# =============================================================
# Job conversion
# =============================================================

def convert_job_to_dict(job):

    if isinstance(
        job,
        dict,
    ):

        return job

    if hasattr(
        job,
        "to_dict",
    ):

        try:

            return job.to_dict()

        except Exception:

            pass

    return {
        "id": getattr(
            job,
            "id",
            None,
        ),

        "title": getattr(
            job,
            "title",
            "",
        ),

        "company": getattr(
            job,
            "company",
            "",
        ),

        "location": getattr(
            job,
            "location",
            "",
        ),

        "description": getattr(
            job,
            "description",
            "",
        ),

        "source": getattr(
            job,
            "source",
            "",
        ),

        "url": getattr(
            job,
            "url",
            "",
        ),
    }


# =============================================================
# Main
# =============================================================

def main():

    print()
    print(
        "🚀 CareerPilot AI v2.0 DAILY JOB AGENT"
    )
    print()

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    print(
        "Initializing database..."
    )

    initialize_database()

    print(
        "Database initialized"
    )

    # ---------------------------------------------------------
    # Profile
    # ---------------------------------------------------------

    print(
        "Loading profile..."
    )

    profile = load_profile()

    # ---------------------------------------------------------
    # Components
    # ---------------------------------------------------------

    search = SearchManager()

    job_filter = JobFilter()

    memory = JobMemory()

    matcher = JobMatcher()

    analyzer = JobAnalyzer()

    decision_engine = DecisionEngine()

    prioritizer = JobPrioritizer()

    intelligence = JobIntelligence()

    assistant = ApplicationAssistant()

    tracker = ApplicationTracker()

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    print(
        "Collecting jobs..."
    )

    try:

        jobs = search.search_jobs()

    except Exception as error:

        print(
            "❌ Job search failed:",
            error,
        )

        return

    converted = []

    for job in jobs:

        converted.append(
            convert_job_to_dict(
                job
            )
        )

    jobs = converted

    print(
        "Collected:",
        len(jobs),
    )

    if not jobs:

        print(
            "No jobs collected."
        )

        return

    # ---------------------------------------------------------
    # Daily memory
    # ---------------------------------------------------------

    print(
        "Checking daily job memory..."
    )

    try:

        jobs = memory.filter_new_jobs(
            jobs
        )

    except Exception as error:

        print(
            "⚠️ Job memory failed:",
            error,
        )

        # Do not destroy the entire pipeline.
        # Continue using current jobs.
        pass

    print(
        "New jobs:",
        len(jobs),
    )

    if not jobs:

        print(
            "No new jobs found."
        )

        return

    # ---------------------------------------------------------
    # Filtering
    # ---------------------------------------------------------

    print(
        "Filtering jobs..."
    )

    try:

        jobs = job_filter.remove_duplicates(
            jobs
        )

        jobs = job_filter.cybersecurity_only(
            jobs
        )

    except Exception as error:

        print(
            "⚠️ Filtering failed:",
            error,
        )

        return

    print(
        "After filtering:",
        len(jobs),
    )

    if not jobs:

        print(
            "No relevant cybersecurity jobs found."
        )

        return

    # ---------------------------------------------------------
    # Ranking
    # ---------------------------------------------------------

    print(
        "Ranking jobs..."
    )

    try:

        ranked = matcher.rank_jobs(
            jobs,
            profile,
        )

    except Exception as error:

        print(
            "❌ Job ranking failed:",
            error,
        )

        return

    if not ranked:

        print(
            "No ranked jobs available."
        )

        return

    top_jobs = ranked[
        :MAX_AI_ANALYSIS
    ]

    print(
        f"AI analyzing top {len(top_jobs)} jobs..."
    )

    results = []

    # ---------------------------------------------------------
    # AI analysis
    # ---------------------------------------------------------

    for ranked_item in top_jobs:

        try:

            job = ranked_item.get(
                "job",
                {},
            )

            job = convert_job_to_dict(
                job
            )

            if not job.get(
                "title"
            ):

                print(
                    "⚠️ Skipping malformed job."
                )

                continue

            match_score = ranked_item.get(
                "match_score",
                0,
            )

            matched_skills = ranked_item.get(
                "matched_skills",
                [],
            )

            location_priority = ranked_item.get(
                "location_priority",
                0,
            )

            title_category = ranked_item.get(
                "title_category",
                "Other",
            )

            security_matches = ranked_item.get(
                "security_matches",
                [],
            )

            match_details = ranked_item.get(
                "match_details",
                {},
            )

            print()
            print(
                "Analyzing:",
                job["title"],
            )

            # -------------------------------------------------
            # AI analysis
            # -------------------------------------------------

            try:

                analysis = analyzer.analyze(
                    job,
                    profile,
                    match_score,
                )

            except Exception as error:

                print(
                    "⚠️ Analyzer failed:",
                    error,
                )

                # Guaranteed fallback.
                analysis = {
                    "summary": (
                        "AI analysis unavailable. "
                        "CareerPilot matcher score used."
                    ),

                    "strengths": matched_skills,

                    "missing_skills": [],

                    "experience_fit": (
                        f"Match score: {match_score}%."
                    ),

                    "recommendation": (
                        "APPLY"
                        if match_score >= 70
                        else "CONSIDER"
                        if match_score >= 50
                        else "SKIP"
                    ),

                    "_analysis_source": (
                        "main_fallback"
                    ),
                }

            # -------------------------------------------------
            # Job intelligence
            # -------------------------------------------------

            try:

                info = intelligence.analyze(
                    job
                )

            except Exception as error:

                print(
                    "⚠️ Job intelligence failed:",
                    error,
                )

                info = {}

            analysis["job_category"] = info.get(
                "category",
                "",
            )

            analysis["job_level"] = info.get(
                "level",
                "",
            )

            # -------------------------------------------------
            # Decision
            # -------------------------------------------------

            try:

                decision = decision_engine.decide(
                    match_score,
                    analysis.get(
                        "missing_skills",
                        [],
                    ),
                    job["title"],
                )

            except Exception as error:

                print(
                    "⚠️ Decision engine failed:",
                    error,
                )

                if match_score >= 70:

                    decision = {
                        "decision": "APPLY NOW"
                    }

                elif match_score >= 50:

                    decision = {
                        "decision": "CONSIDER APPLYING"
                    }

                else:

                    decision = {
                        "decision": "SKIP"
                    }

            analysis["decision"] = decision

            # -------------------------------------------------
            # Job information
            # -------------------------------------------------

            analysis["job_title"] = job.get(
                "title",
                "",
            )

            analysis["company"] = job.get(
                "company",
                "",
            )

            analysis["location"] = job.get(
                "location",
                "",
            )

            analysis["description"] = job.get(
                "description",
                "",
            )

            analysis["source"] = job.get(
                "source",
                "",
            )

            analysis["url"] = job.get(
                "url",
                "",
            )

            # -------------------------------------------------
            # Matching information
            # -------------------------------------------------

            analysis["match_score"] = match_score

            analysis["matched_skills"] = (
                matched_skills
            )

            analysis["location_priority"] = (
                location_priority
            )

            analysis["title_category"] = (
                title_category
            )

            analysis["security_matches"] = (
                security_matches
            )

            analysis["match_details"] = (
                match_details
            )

            # -------------------------------------------------
            # CV points
            # -------------------------------------------------

            try:

                analysis["cv_points"] = (
                    assistant.generate_cv_points(
                        job,
                        profile,
                    )
                )

            except Exception as error:

                print(
                    "⚠️ CV point generation failed:",
                    error,
                )

                analysis["cv_points"] = []

            # -------------------------------------------------
            # Application tracker
            # -------------------------------------------------

            decision_value = decision.get(
                "decision",
                "",
            )

            if decision_value in [
                "APPLY NOW",
                "CONSIDER APPLYING",
            ]:

                try:

                    tracker.save_job(
                        {
                            **job,
                            "job_title": job.get(
                                "title",
                                "",
                            ),
                            "match_score": (
                                match_score
                            ),
                            "decision": decision,
                        }
                    )

                except Exception as error:

                    print(
                        "⚠️ Application tracker failed:",
                        error,
                    )

            results.append(
                analysis
            )

        except Exception as error:

            print(
                "⚠️ Job processing failed:",
                error,
            )

            # Continue with remaining jobs.
            continue

    # ---------------------------------------------------------
    # Final prioritization
    # ---------------------------------------------------------

    if not results:

        print()
        print(
            "No jobs could be analyzed."
        )

        return

    try:

        results = prioritizer.prioritize(
            results
        )

    except Exception as error:

        print(
            "⚠️ Prioritization failed:",
            error,
        )

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    print()
    print(
        "=" * 60
    )

    print(
        "CareerPilot Recommendations"
    )

    print(
        "=" * 60
    )

    for i, job in enumerate(
        results,
        1,
    ):

        print()

        print(
            f"{i}. {job.get('job_title', '')}"
        )

        print(
            "Company:",
            job.get(
                "company",
                "",
            ),
        )

        print(
            "Location:",
            job.get(
                "location",
                "",
            ),
        )

        print(
            "Match:",
            job.get(
                "match_score",
                0,
            ),
            "%",
        )

        decision = job.get(
            "decision",
            {},
        )

        print(
            "Decision:",
            decision.get(
                "decision",
                "",
            ),
        )

        print(
            "Priority:",
            job.get(
                "priority_group",
                "",
            ),
        )

        print(
            "Analysis:",
            job.get(
                "_analysis_source",
                "unknown",
            ),
        )

        print(
            "URL:",
            job.get(
                "url",
                "",
            ),
        )

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    try:

        save_jobs_to_database(
            results
        )

    except Exception as error:

        print(
            "⚠️ Database operation failed:",
            error,
        )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    try:

        save_report(
            results
        )

    except Exception as error:

        print(
            "❌ Failed to save report:",
            error,
        )

        return

    # ---------------------------------------------------------
    # Complete
    # ---------------------------------------------------------

    print()
    print(
        "✅ CareerPilot AI v2.0 complete"
    )

    print(
        "✅ Real job sources enabled"
    )

    print(
        "✅ Job deduplication enabled"
    )

    print(
        "✅ Daily job memory enabled"
    )

    print(
        "✅ Job matching enabled"
    )

    print(
        "✅ AI analysis enabled with fallback"
    )

    print(
        "✅ Application tracker enabled"
    )

    print(
        "✅ Report saved:"
    )

    print(
        "   output/jobs_report.json"
    )


# =============================================================
# Entry point
# =============================================================

if __name__ == "__main__":

    main()