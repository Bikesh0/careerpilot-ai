import json
from pathlib import Path


class ProfileLoader:

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.profile_path = self.project_root / "profiles" / "profile.json"

    def load(self):

        if not self.profile_path.exists():
            raise FileNotFoundError(
                f"Profile file not found: {self.profile_path}"
            )

        with open(
            self.profile_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)