from app.ai.skill_map import SKILL_MAP


class JobMatcher:

    SECURITY_KEYWORDS = {
        "security": 10,
        "cyber": 10,
        "soc": 9,
        "siem": 9,
        "splunk": 8,
        "sentinel": 8,
        "incident": 8,
        "threat": 8,
        "firewall": 7,
        "ids": 7,
        "ips": 7,
        "iam": 7,
        "identity": 7,
        "cloud": 6,
        "linux": 6,
        "docker": 5,
        "kubernetes": 5,
        "python": 5,
        "network": 6,
        "tcp/ip": 6,
        "azure": 6,
        "aws": 6
    }

    LOCATION_BONUS = {
        "helsinki": 10,
        "espoo": 10,
        "vantaa": 9,
        "tampere": 8,
        "finland": 7,
        "remote": 6
    }

    def get_text(self, job):

        return (
            f"{job.title} "
            f"{job.description}"
        ).lower()

    def skill_score(self, job, profile):

        text = self.get_text(job)

        score = 0
        matched = []

        for skill in profile["skills"]:

            skill_lower = skill.lower()

            aliases = SKILL_MAP.get(
                skill_lower,
                [skill_lower]
            )

            found = False

            for alias in aliases:

                if alias in text:

                    score += 10

                    matched.append(skill)

                    found = True

                    break

            if found:
                continue

        return min(score, 100), matched

    def security_bonus(self, job):

        text = self.get_text(job)

        bonus = 0

        for keyword, value in self.SECURITY_KEYWORDS.items():

            if keyword in text:
                bonus += value

        return min(bonus, 100)

    def location_bonus(self, job):

        location = job.location.lower()

        for city, value in self.LOCATION_BONUS.items():

            if city in location:
                return value

        return 0

    def rank_jobs(self, jobs, profile):

        ranked = []

        for job in jobs:

            skill, matched = self.skill_score(
                job,
                profile
            )

            security = self.security_bonus(job)

            location = self.location_bonus(job)

            final = round(
                skill * 0.70 +
                security * 0.20 +
                location * 0.10
            )

            ranked.append(
                {
                    "job": job,
                    "match_score": min(final, 100),
                    "matched_skills": matched
                }
            )

        ranked.sort(
            key=lambda x: x["match_score"],
            reverse=True
        )

        return ranked