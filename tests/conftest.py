import json
from pathlib import Path

import pytest


@pytest.fixture
def greenhouse_payload():
    fixture_path = Path(__file__).parent / "fixtures" / "greenhouse_jobs.json"

    with fixture_path.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


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
