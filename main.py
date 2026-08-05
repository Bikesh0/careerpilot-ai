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
    job_exists
)


from app.database.application_tracker import ApplicationTracker



MAX_AI_ANALYSIS = 5



def load_profile():

    with open(
        "profiles/profile.json",
        "r"
    ) as file:

        return json.load(file)



def save_report(data):

    os.makedirs(
        "output",
        exist_ok=True
    )

    with open(
        "output/jobs_report.json",
        "w"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )



def save_jobs_to_database(results):

    conn = get_connection()

    cursor = conn.cursor()

    saved = 0


    for job in results:


        if job_exists(
            job["job_title"],
            job["company"]
        ):

            continue



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

                job["company"],

                job.get(
                    "location",
                    ""
                ),

                job.get(
                    "description",
                    ""
                ),

                job.get(
                    "source",
                    ""
                ),

                job.get(
                    "url",
                    ""
                ),

                job["match_score"],

                job["decision"]["decision"]

            )
        )


        saved += 1



    conn.commit()

    conn.close()


    print(
        f"Saved {saved} jobs."
    )





def main():


    print()

    print(
        "🚀 CareerPilot AI v2.0 DAILY JOB AGENT"
    )

    print()



    print(
        "Initializing database..."
    )


    initialize_database()



    print(
        "Loading profile..."
    )


    profile = load_profile()



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



    print(
        "Collecting jobs..."
    )


    jobs = search.search_jobs()



    # Convert Job objects to dictionaries

    converted = []


    for job in jobs:


        if hasattr(
            job,
            "to_dict"
        ):

            converted.append(
                job.to_dict()
            )


        elif isinstance(
            job,
            dict
        ):

            converted.append(
                job
            )


        else:

            converted.append({

                "title": job.title,

                "company": job.company,

                "location": job.location,

                "description": job.description,

                "source": job.source,

                "url": job.url

            })



    jobs = converted



    print(
        "Collected:",
        len(jobs)
    )



    jobs = memory.filter_new_jobs(
        jobs
    )


    print(
        "New jobs:",
        len(jobs)
    )



    if len(jobs) == 0:

        print(
            "No new jobs found."
        )

        return



    print(
        "Filtering jobs..."
    )


    jobs = job_filter.remove_duplicates(
        jobs
    )


    jobs = job_filter.cybersecurity_only(
        jobs
    )


    print(
        "After filtering:",
        len(jobs)
    )



    print(
        "Ranking jobs..."
    )


    ranked = matcher.rank_jobs(
        jobs,
        profile
    )


    top_jobs = ranked[:MAX_AI_ANALYSIS]


    print(
        "AI analyzing jobs..."
    )



    results = []



    for item in top_jobs:


        job = item["job"]


        print()

        print(
            "Analyzing:",
            job["title"]
        )



        analysis = analyzer.analyze(

            job,

            profile,

            item["match_score"]

        )



        info = intelligence.analyze(
            job
        )


        analysis["job_category"] = info.get(
            "category",
            ""
        )


        analysis["job_level"] = info.get(
            "level",
            ""
        )



        decision = decision_engine.decide(

            item["match_score"],

            analysis.get(
                "missing_skills",
                []
            ),

            job["title"]

        )


        analysis["decision"] = decision



        analysis["job_title"] = job["title"]

        analysis["company"] = job["company"]

        analysis["location"] = job.get(
            "location",
            ""
        )

        analysis["description"] = job.get(
            "description",
            ""
        )

        analysis["source"] = job.get(
            "source",
            ""
        )

        analysis["url"] = job.get(
            "url",
            ""
        )



        analysis["cv_points"] = assistant.generate_cv_points(

            job,

            profile

        )



        if decision["decision"] in [

            "APPLY NOW",

            "CONSIDER APPLYING"

        ]:

            tracker.save_job(
                job
            )



        results.append(
            analysis
        )



    results = prioritizer.prioritize(
        results
    )



    print()

    print(
        "=" * 50
    )

    print(
        "CareerPilot Recommendations"
    )

    print(
        "=" * 50
    )



    for i, job in enumerate(
        results,
        1
    ):

        print()

        print(
            f"{i}. {job['job_title']}"
        )


        print(
            "Company:",
            job["company"]
        )


        print(
            "Match:",
            job["match_score"],
            "%"
        )


        print(
            "Decision:",
            job["decision"]["decision"]
        )


        print(
            "Priority:",
            job.get(
                "priority_group",
                ""
            )
        )



    save_jobs_to_database(
        results
    )


    save_report(
        results
    )


    print()

    print(
        "✅ CareerPilot AI v2.0 complete"
    )

    print(
        "✅ Daily job memory enabled"
    )

    print(
        "✅ Application tracker enabled"
    )

    print(
        "✅ Report saved"
    )




if __name__ == "__main__":

    main()