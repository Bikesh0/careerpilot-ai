class ScoringEngine:

    def total_score(
        self,
        skill_score,
        security_score,
        target_score,
        location_score,
        experience_score
    ):

        score = (

            skill_score * 0.40 +

            security_score * 0.20 +

            target_score * 0.20 +

            location_score * 0.10 +

            experience_score * 0.10

        )

        return round(score)