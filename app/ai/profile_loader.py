import json


class ProfileLoader:

    def load(self):

        with open(
            "profiles/profile.json",
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)