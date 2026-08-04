import json
import os

from app.search.manager import SearchManager
from app.ai.matcher import JobMatcher
from app.ai.analyzer import JobAnalyzer


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



def main():

    print("\n🚀 CareerPilot AI v0.3\n")


    # Load user profile
    profile = load_profile()


    # Initialize components
    search = SearchManager()

    matcher = JobMatcher()

    analyzer = JobAnalyzer()



    # Find jobs
    jobs = search.search_jobs()



    # Match jobs
    ranked = matcher.rank_jobs(
        jobs,
        profile
    )



    # AI analysis layer
    analysis_results = []


    for item in ranked:

        result = analyzer.analyze(
            item["job"],
            profile,
            item["match_score"]
        )

        analysis_results.append(result)



    # Display results

    for result in analysis_results:

        print("---------------------")

        print(
            "Job:",
            result["job_title"]
        )

        print(
            "Company:",
            result["company"]
        )

        print(
            "Match:",
            result["match_score"],
            "%"
        )

        print(
            "Strengths:",
            result["strengths"]
        )

        print(
            "Missing skills:",
            result["missing_skills"]
        )

        print(
            "Recommendation:",
            result["recommendation"]
        )

        print()



    # Save final report
    save_report(
        analysis_results
    )


    print(
        "✅ Report saved: output/jobs_report.json"
    )



if __name__ == "__main__":
    main()