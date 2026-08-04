import json
import os

from app.search.manager import SearchManager
from app.ai.matcher import JobMatcher


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

    print("\n🚀 CareerPilot AI v0.1\n")

    profile = load_profile()

    search = SearchManager()

    matcher = JobMatcher()


    jobs = search.search_jobs()


    ranked = matcher.rank_jobs(
        jobs,
        profile
    )


    for item in ranked:

        print(
            item["job"]["title"],
            "=>",
            item["match_score"],
            "%"
        )


    save_report(ranked)


    print(
        "\n✅ Report saved: output/jobs_report.json"
    )



if __name__ == "__main__":
    main()