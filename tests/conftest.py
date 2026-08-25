import json
from pathlib import Path

import pytest


@pytest.fixture
def greenhouse_payload():
    fixture_path = Path(__file__).parent / "fixtures" / "greenhouse_jobs.json"

    with fixture_path.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


@pytest.fixture
def hoxhunt_secops_description():
    """
    Real, live-fetched plain-text description of Hoxhunt's "Security
    Engineer, SecOps" Ashby posting (job board:
    api.ashbyhq.com/posting-api/job-board/hoxhunt), captured verbatim -
    not hand-written - so regression tests exercise the extraction
    engine against genuinely messy real-world formatting (hard-wrapped
    bullet lines, a "Bonus points if you also:" section, mixed
    responsibilities/qualifications headings) rather than an idealized
    example.
    """

    fixture_path = (
        Path(__file__).parent / "fixtures" / "hoxhunt_secops_description.txt"
    )

    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def candidate_profile():
    return {
        "skills": ["python", "linux", "siem"],
        "experience": [
            {
                "title": "IT Support Trainee",
                "description": "Linux troubleshooting and network support",
            }
        ],
    }
