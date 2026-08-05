import json
import os

from app.documents.cover_letter_generator import CoverLetterGenerator


def load_profile():
    with open(
        "profiles/profile.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def load_jobs():
    with open(
        "output/jobs_report.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def main():

    profile = load_profile()

    jobs = load_jobs()

    print("\nAvailable Jobs\n")

    for i, job in enumerate(jobs, start=1):

        print(
            f"{i}. {job['job_title']} "
            f"({job['match_score']}%)"
        )

    print()

    choice = int(
        input("Choose a job number: ")
    )

    selected = jobs[choice - 1]

    generator = CoverLetterGenerator()

    print("\nGenerating cover letter...\n")

    cover = generator.generate(
        profile,
        {
            "title": selected["job_title"],
            "company": selected["company"],
            "description": selected["ai_analysis"]
        }
    )

    filename = (
        selected["job_title"]
        .replace(" ", "_")
        + "_cover_letter.txt"
    )

    os.makedirs(
        "output",
        exist_ok=True
    )

    with open(
        os.path.join(
            "output",
            filename
        ),
        "w",
        encoding="utf-8"
    ) as file:

        file.write(cover)

    print()

    print("✅ Done!")

    print(
        f"Saved to output/{filename}"
    )


if __name__ == "__main__":
    main()