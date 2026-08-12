import re


class JobMatcher:
    """
    CareerPilot AI job matching engine.

    Designed for real job postings.

    Supports:
    - Dictionary jobs
    - Job objects
    - SearchProfile objects
    - Dictionary profiles

    Produces transparent matching information including:
    - title relevance
    - skill matches
    - security relevance
    - experience relevance
    - location
    - seniority
    - required experience
    - mismatch penalties
    """

    # =========================================================
    # TARGET JOB TITLES
    # =========================================================

    PRIMARY_TITLES = [
        "soc analyst",
        "soc analyst tier 1",
        "soc analyst tier i",
        "security analyst",
        "cybersecurity analyst",
        "cyber security analyst",
        "information security analyst",
        "information security specialist",
        "it security specialist",
        "it security analyst",
        "security engineer",
        "junior security engineer",
        "cybersecurity engineer",
        "cyber security engineer",
        "security operations analyst",
        "security operations",
        "security operations center",
        "soc",
        "incident response",
        "incident responder",
        "security administrator",
        "security operations specialist",
        "cloud security engineer",
        "cloud security specialist",
        "network security engineer",
        "network security specialist",
        "network security",
        "iam analyst",
        "iam engineer",
        "identity and access",
        "identity and access management",
        "devsecops",
        "vulnerability analyst",
        "threat detection analyst",
        "threat analyst",
        "cyber security specialist",
        "cybersecurity specialist",
        "tietoturva-asiantuntija",
        "tietoturva asiantuntija",
        "tietoturva-analyytikko",
        "tietoturva analyytikko",
        "kyberturvallisuus",
        "kyberturvallisuusasiantuntija",
    ]

    SECONDARY_TITLES = [
        "cloud engineer",
        "cloud support",
        "cloud support engineer",
        "cloud operations",
        "devops",
        "devops engineer",
        "network engineer",
        "linux administrator",
        "linux engineer",
        "linux system administrator",
        "infrastructure engineer",
        "infrastructure support",
        "infrastructure specialist",
        "it support",
        "technical support",
        "technical support engineer",
        "support engineer",
        "service desk",
        "helpdesk",
        "system engineer",
        "systems engineer",
        "system administrator",
        "systems administrator",
        "network administrator",
        "network support",
        "platform engineer",
    ]

    RELATED_TITLES = [
        "threat detection",
        "security platform",
        "security infrastructure",
        "security software",
        "security tools",
        "security technology",
        "defence and security",
        "defense and security",
        "cloud operations",
        "site reliability engineer",
        "sre",
        "security consultant",
        "security consulting",
        "it infrastructure",
        "infrastructure specialist",
        "järjestelmäasiantuntija",
        "järjestelmäasiantuntija",
        "verkkosuunnittelija",
        "verkkoasiantuntija",
        "network specialist",
    ]

    # =========================================================
    # CLEARLY UNRELATED TITLES
    # =========================================================

    EXCLUDED_TITLE_TERMS = [
        "marketing",
        "sales",
        "account executive",
        "business development",
        "business developer",
        "recruiter",
        "recruitment",
        "talent acquisition",
        "human resources",
        "hr manager",
        "designer",
        "graphic designer",
        "ux designer",
        "ui designer",
        "content writer",
        "copywriter",
        "teacher",
        "accountant",
        "finance manager",
        "financial analyst",
        "legal counsel",
        "lawyer",
        "product marketing",
        "communications manager",
        "head of marketing",
        "social media manager",
        "customer success manager",
        "sales manager",
        "sales representative",
    ]

    # =========================================================
    # SECURITY TERMS
    # =========================================================

    SECURITY_TERMS = [
        "security",
        "cybersecurity",
        "cyber security",
        "soc",
        "siem",
        "infosec",
        "information security",
        "security operations",
        "incident response",
        "incident investigation",
        "incident handling",
        "threat detection",
        "threat intelligence",
        "threat hunting",
        "penetration testing",
        "penetration test",
        "pentesting",
        "vulnerability",
        "vulnerability management",
        "firewall",
        "ids",
        "ips",
        "intrusion detection",
        "intrusion prevention",
        "identity",
        "iam",
        "identity and access management",
        "authentication",
        "authorization",
        "network security",
        "cloud security",
        "endpoint security",
        "edr",
        "xdr",
        "malware",
        "phishing",
        "forensics",
        "digital forensics",
        "risk management",
        "security monitoring",
        "security incident",
    ]

    # =========================================================
    # LOCATION
    # =========================================================

    LOCATION_PRIORITY = {
        "helsinki": 20,
        "espoo": 19,
        "vantaa": 18,
    }

    FINLAND_TERMS = [
        "finland",
        "helsinki",
        "espoo",
        "vantaa",
        "turku",
        "tampere",
        "oulu",
        "lahti",
        "jyvaskyla",
        "jyväskylä",
        "pori",
        "kuopio",
        "finland, fi",
        "fi",
    ]

    REMOTE_TERMS = [
        "remote",
        "remote-friendly",
        "remote friendly",
        "work from anywhere",
        "distributed",
        "hybrid",
    ]

    # =========================================================
    # SENIORITY
    # =========================================================

    SENIORITY_TERMS = {
        "intern": [
            "intern",
            "internship",
            "trainee",
            "training",
            "harjoittelija",
            "harjoittelu",
            "student trainee",
        ],
        "junior": [
            "junior",
            "entry level",
            "entry-level",
            "graduate",
            "new graduate",
            "early career",
            "associate",
            "0-1 years",
            "0 to 1 years",
            "1-2 years",
            "1 to 2 years",
        ],
        "senior": [
            "senior",
            "senior-level",
            "sr.",
            "sr ",
        ],
        "lead": [
            "lead",
            "team lead",
            "tech lead",
            "technical lead",
            "security lead",
        ],
        "manager": [
            "manager",
            "security manager",
            "engineering manager",
            "it manager",
        ],
        "architect": [
            "architect",
            "security architect",
            "cloud architect",
            "solution architect",
            "solutions architect",
        ],
        "director": [
            "director",
            "head of",
            "vice president",
            "vp ",
            "chief",
            "ciso",
        ],
    }

    SENIORITY_PENALTIES = {
        "intern": 0,
        "junior": 0,
        "mid": 0,
        "unspecified": 0,
        "senior": 15,
        "lead": 28,
        "manager": 32,
        "architect": 30,
        "director": 40,
    }

    # =========================================================
    # SKILL WEIGHTS
    # =========================================================

    SKILL_WEIGHTS = {
        "cybersecurity": 3.0,
        "security": 3.0,
        "network security": 3.0,
        "siem": 3.0,
        "splunk": 3.0,
        "firewall": 2.8,
        "ids": 2.8,
        "ips": 2.8,
        "incident response": 3.0,
        "penetration testing": 2.8,
        "iam": 2.8,
        "identity": 2.5,
        "linux": 2.5,
        "networking": 2.5,
        "tcp/ip": 2.5,
        "cloud": 2.5,
        "google cloud": 2.5,
        "gcp": 2.5,
        "docker": 2.0,
        "kubernetes": 2.0,
        "vmware": 2.0,
        "vpn": 2.0,
        "python": 1.8,
        "git": 1.5,
        "ci/cd": 1.5,
        "zfs": 1.5,
        "iscsi": 1.5,
    }

    # =========================================================
    # EXPERIENCE KEYWORDS
    # =========================================================

    EXPERIENCE_KEYWORDS = [
        "linux",
        "network",
        "networking",
        "security",
        "cybersecurity",
        "cloud",
        "docker",
        "kubernetes",
        "firewall",
        "ids",
        "ips",
        "splunk",
        "siem",
        "python",
        "penetration",
        "iam",
        "identity",
        "helpdesk",
        "technical support",
        "tcp/ip",
        "vmware",
        "zfs",
        "iscsi",
        "vpn",
        "routing",
        "switching",
        "git",
        "ci/cd",
    ]

    # =========================================================
    # MAIN RANKING
    # =========================================================

    def rank_jobs(self, jobs, profile):
        """
        Rank real jobs against the user's profile.

        Returns:

        {
            "job": {...},
            "match_score": 85,
            "matched_skills": [...],
            "location_priority": 20,
            "title_category": "Primary",
            "security_matches": [...],
            "seniority": "junior",
            "match_details": {...}
        }
        """

        if jobs is None:
            return []

        profile_skills = self._profile_value(
            profile,
            "skills",
            default=None,
        )

        if profile_skills is None:
            profile_skills = self._profile_value(
                profile,
                "strong_skills",
                default=[],
            )

        profile_skills = self._normalise_list(
            profile_skills
        )

        experience = self._profile_value(
            profile,
            "experience",
            default=[],
        )

        experience_text = self._build_experience_text(
            experience
        )

        ranked_jobs = []

        for original_job in jobs:

            job = self._normalise_job(
                original_job
            )

            title = self._clean_text(
                job.get("title", "")
            )

            description = self._clean_text(
                job.get("description", "")
            )

            location = self._clean_text(
                job.get("location", "")
            )

            company = self._clean_text(
                job.get("company", "")
            )

            workplace_type = self._clean_text(
                job.get("workplace_type", "")
            )

            text = (
                title
                + " "
                + description
            ).lower()

            # -------------------------------------------------
            # Exclude obviously unrelated jobs
            # -------------------------------------------------

            if self._contains_any(
                title,
                self.EXCLUDED_TITLE_TERMS,
            ):
                continue

            # -------------------------------------------------
            # Title matching
            # -------------------------------------------------

            title_category = "Other"
            title_score = 0

            if self._title_matches(
                title,
                self.PRIMARY_TITLES,
            ):
                title_category = "Primary"
                title_score = 40

            elif self._title_matches(
                title,
                self.SECONDARY_TITLES,
            ):
                title_category = "Secondary"
                title_score = 27

            elif self._title_matches(
                title,
                self.RELATED_TITLES,
            ):
                title_category = "Related"
                title_score = 20

            elif self._contains_any(
                title,
                self.SECURITY_TERMS,
            ):
                title_category = "Security-related"
                title_score = 15

            elif self._contains_any(
                text,
                self.SECURITY_TERMS,
            ):
                title_category = "Security-related"
                title_score = 8

            # -------------------------------------------------
            # Matched profile skills
            # -------------------------------------------------

            matched_skills = []

            for skill in profile_skills:

                if self._skill_in_text(
                    skill,
                    text,
                ):
                    matched_skills.append(skill)

            skill_count = len(matched_skills)

            if profile_skills:
                skill_ratio = (
                    skill_count
                    / len(profile_skills)
                )
            else:
                skill_ratio = 0

            skill_score = self._calculate_skill_score(
                matched_skills
            )

            # Maximum 25 points.
            skill_score = min(
                skill_score,
                25,
            )

            # -------------------------------------------------
            # Security matching
            # -------------------------------------------------

            security_matches = []

            for term in self.SECURITY_TERMS:

                if self._term_in_text(
                    term,
                    text,
                ):
                    security_matches.append(term)

            security_matches = list(
                dict.fromkeys(
                    security_matches
                )
            )

            security_score = min(
                len(security_matches) * 1.5,
                12,
            )

            # -------------------------------------------------
            # Experience relevance
            # -------------------------------------------------

            experience_matches = []

            if experience_text:

                for keyword in self.EXPERIENCE_KEYWORDS:

                    if (
                        keyword in experience_text
                        and self._term_in_text(
                            keyword,
                            text,
                        )
                    ):
                        experience_matches.append(
                            keyword
                        )

            experience_matches = list(
                dict.fromkeys(
                    experience_matches
                )
            )

            experience_score = min(
                len(experience_matches) * 1.5,
                10,
            )

            # -------------------------------------------------
            # Location
            # -------------------------------------------------

            location_score = self._location_score(
                location,
                text,
                workplace_type,
            )

            # -------------------------------------------------
            # Seniority
            # -------------------------------------------------

            seniority = self._detect_seniority(
                title,
                text,
            )

            seniority_penalty = (
                self.SENIORITY_PENALTIES.get(
                    seniority,
                    0,
                )
            )

            junior_bonus = 0

            if seniority == "junior":
                junior_bonus = 5

            elif seniority == "intern":
                junior_bonus = 6

            # -------------------------------------------------
            # Required experience
            # -------------------------------------------------

            required_experience_years = (
                self._extract_required_experience(
                    text
                )
            )

            experience_requirement_penalty = (
                self._experience_requirement_penalty(
                    required_experience_years
                )
            )

            # -------------------------------------------------
            # Strong mismatch penalties
            # -------------------------------------------------

            mismatch_penalty = 0
            mismatch_reasons = []

            # Senior/lead/architect roles are particularly
            # unsuitable for an early-career target profile.

            if seniority == "lead":
                mismatch_penalty += 8
                mismatch_reasons.append(
                    "lead-level role"
                )

            elif seniority == "manager":
                mismatch_penalty += 10
                mismatch_reasons.append(
                    "manager-level role"
                )

            elif seniority == "architect":
                mismatch_penalty += 10
                mismatch_reasons.append(
                    "architect-level role"
                )

            elif seniority == "director":
                mismatch_penalty += 15
                mismatch_reasons.append(
                    "director-level role"
                )

            # Jobs with no meaningful security/title relevance
            # should not rank highly merely because of generic
            # technical skills.

            if (
                title_category == "Other"
                and not security_matches
            ):
                mismatch_penalty += 8
                mismatch_reasons.append(
                    "weak relevance to target roles"
                )

            # A very high experience requirement is a strong
            # signal against early-career roles.

            if (
                required_experience_years is not None
                and required_experience_years >= 5
            ):
                mismatch_penalty += 8

                mismatch_reasons.append(
                    "high experience requirement"
                )

            # -------------------------------------------------
            # Security relevance bonus
            # -------------------------------------------------

            security_role_bonus = 0

            if title_category == "Primary":
                security_role_bonus = 5

            elif (
                title_category == "Security-related"
                and security_matches
            ):
                security_role_bonus = 3

            # -------------------------------------------------
            # Final score
            # -------------------------------------------------

            raw_score = (
                title_score
                + skill_score
                + security_score
                + experience_score
                + location_score
                + junior_bonus
                + security_role_bonus
                - seniority_penalty
                - experience_requirement_penalty
                - mismatch_penalty
            )

            score = round(
                max(
                    min(raw_score, 100),
                    0,
                )
            )

            # -------------------------------------------------
            # Match quality
            # -------------------------------------------------

            match_quality = self._match_quality(
                score
            )

            # -------------------------------------------------
            # Transparent details
            # -------------------------------------------------

            match_details = {
                "title_score": round(
                    title_score,
                    2,
                ),
                "skill_score": round(
                    skill_score,
                    2,
                ),
                "security_score": round(
                    security_score,
                    2,
                ),
                "experience_score": round(
                    experience_score,
                    2,
                ),
                "location_score": round(
                    location_score,
                    2,
                ),
                "junior_bonus": junior_bonus,
                "security_role_bonus": security_role_bonus,
                "seniority": seniority,
                "seniority_penalty": seniority_penalty,
                "required_experience_years": (
                    required_experience_years
                ),
                "experience_requirement_penalty": (
                    experience_requirement_penalty
                ),
                "mismatch_penalty": mismatch_penalty,
                "mismatch_reasons": mismatch_reasons,
                "matched_skill_count": skill_count,
                "profile_skill_count": len(
                    profile_skills
                ),
                "skill_ratio": round(
                    skill_ratio,
                    2,
                ),
                "security_match_count": len(
                    security_matches
                ),
                "experience_match_count": len(
                    experience_matches
                ),
                "match_quality": match_quality,
            }

            ranked_jobs.append(
                {
                    "job": job,
                    "match_score": score,
                    "matched_skills": matched_skills,
                    "location_priority": location_score,
                    "title_category": title_category,
                    "security_matches": security_matches,
                    "seniority": seniority,
                    "match_quality": match_quality,
                    "match_details": match_details,
                }
            )

        # -----------------------------------------------------
        # Sorting
        # -----------------------------------------------------

        ranked_jobs.sort(
            key=self._ranking_key,
            reverse=True,
        )

        return ranked_jobs

    # =========================================================
    # Ranking key
    # =========================================================

    def _ranking_key(
        self,
        item,
    ):
        details = item.get(
            "match_details",
            {},
        )

        return (
            item.get(
                "match_score",
                0,
            ),
            details.get(
                "title_score",
                0,
            ),
            details.get(
                "skill_score",
                0,
            ),
            details.get(
                "security_score",
                0,
            ),
            item.get(
                "location_priority",
                0,
            ),
        )

    # =========================================================
    # Skill score
    # =========================================================

    def _calculate_skill_score(
        self,
        matched_skills,
    ):
        total = 0

        for skill in matched_skills:

            weight = self.SKILL_WEIGHTS.get(
                skill,
                1.5,
            )

            total += weight

        return total

    # =========================================================
    # Match quality
    # =========================================================

    def _match_quality(
        self,
        score,
    ):
        if score >= 80:
            return "Excellent"

        if score >= 65:
            return "Strong"

        if score >= 50:
            return "Good"

        if score >= 35:
            return "Moderate"

        if score >= 20:
            return "Weak"

        return "Poor"

    # =========================================================
    # Profile helpers
    # =========================================================

    def _profile_value(
        self,
        profile,
        key,
        default=None,
    ):
        if profile is None:
            return default

        if isinstance(profile, dict):
            return profile.get(
                key,
                default,
            )

        return getattr(
            profile,
            key,
            default,
        )

    # =========================================================
    # Job normalization
    # =========================================================

    def _normalise_job(
        self,
        job,
    ):
        if isinstance(job, dict):
            return dict(job)

        result = {}

        possible_fields = [
            "id",
            "title",
            "company",
            "location",
            "url",
            "description",
            "source",
            "source_id",
            "posted_at",
            "employment_type",
            "workplace_type",
            "salary",
            "skills",
            "match_score",
            "matched_skills",
        ]

        for field in possible_fields:

            if hasattr(job, field):
                result[field] = getattr(
                    job,
                    field,
                )

        return result

    # =========================================================
    # Text helpers
    # =========================================================

    def _clean_text(
        self,
        value,
    ):
        if value is None:
            return ""

        text = str(value)

        text = (
            text
            .replace("\xa0", " ")
            .replace("\\_", "_")
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip().lower()

    def _normalise_list(
        self,
        value,
    ):
        if value is None:
            return []

        if isinstance(value, str):
            value = [value]

        result = []

        try:
            iterator = iter(value)

        except TypeError:
            iterator = iter([value])

        for item in iterator:

            cleaned = self._clean_text(
                item
            )

            if cleaned:
                result.append(
                    cleaned
                )

        return list(
            dict.fromkeys(result)
        )

    def _contains_any(
        self,
        text,
        terms,
    ):
        text = self._clean_text(
            text
        )

        return any(
            self._term_in_text(
                term,
                text,
            )
            for term in terms
        )

    def _term_in_text(
        self,
        term,
        text,
    ):
        term = self._clean_text(
            term
        )

        text = self._clean_text(
            text
        )

        if not term or not text:
            return False

        if " " in term:
            return term in text

        return re.search(
            r"\b"
            + re.escape(term)
            + r"\b",
            text,
        ) is not None

    # =========================================================
    # Skill matching
    # =========================================================

    def _skill_in_text(
        self,
        skill,
        text,
    ):
        skill = self._clean_text(
            skill
        )

        if not skill:
            return False

        aliases = {
            "google cloud": [
                "google cloud",
                "gcp",
                "google cloud platform",
            ],
            "gcp": [
                "gcp",
                "google cloud",
                "google cloud platform",
            ],
            "kubernetes": [
                "kubernetes",
                "k8s",
            ],
            "kubernetes basics": [
                "kubernetes",
                "k8s",
            ],
            "docker": [
                "docker",
            ],
            "iam": [
                "iam",
                "identity and access management",
            ],
            "siem": [
                "siem",
                "microsoft sentinel",
                "sentinel",
            ],
            "ids": [
                "ids",
                "intrusion detection",
            ],
            "ips": [
                "ips",
                "intrusion prevention",
            ],
            "cybersecurity": [
                "cybersecurity",
                "cyber security",
                "information security",
                "infosec",
            ],
            "networking": [
                "networking",
                "network security",
                "tcp/ip",
                "routing",
                "switching",
                "computer networks",
            ],
            "linux": [
                "linux",
            ],
            "vmware": [
                "vmware",
                "vsphere",
            ],
            "splunk": [
                "splunk",
            ],
            "firewall": [
                "firewall",
                "firewalls",
            ],
            "vpn": [
                "vpn",
                "virtual private network",
            ],
            "penetration testing": [
                "penetration testing",
                "penetration test",
                "pentesting",
                "pen testing",
            ],
            "python": [
                "python",
            ],
            "git": [
                "git",
                "github",
                "gitlab",
            ],
            "ci/cd": [
                "ci/cd",
                "cicd",
                "continuous integration",
                "continuous delivery",
                "continuous deployment",
            ],
            "cloud": [
                "cloud",
                "cloud computing",
            ],
            "security": [
                "security",
                "cybersecurity",
                "information security",
            ],
        }

        candidates = aliases.get(
            skill,
            [skill],
        )

        return any(
            self._term_in_text(
                candidate,
                text,
            )
            for candidate in candidates
        )

    # =========================================================
    # Title helpers
    # =========================================================

    def _title_matches(
        self,
        title,
        patterns,
    ):
        title = self._clean_text(
            title
        )

        return any(
            self._term_in_text(
                pattern,
                title,
            )
            for pattern in patterns
        )

    # =========================================================
    # Experience
    # =========================================================

    def _build_experience_text(
        self,
        experience,
    ):
        if experience is None:
            return ""

        if isinstance(experience, str):
            return self._clean_text(
                experience
            )

        parts = []

        try:

            for item in experience:

                if isinstance(item, dict):

                    parts.extend(
                        str(value)
                        for value in item.values()
                        if value is not None
                    )

                else:
                    parts.append(
                        str(item)
                    )

        except TypeError:

            return self._clean_text(
                experience
            )

        return self._clean_text(
            " ".join(parts)
        )

    # =========================================================
    # Location
    # =========================================================

    def _location_score(
        self,
        location,
        text="",
        workplace_type="",
    ):
        location = self._clean_text(
            location
        )

        text = self._clean_text(
            text
        )

        workplace_type = self._clean_text(
            workplace_type
        )

        # Highest priority: preferred cities.

        for city, score in self.LOCATION_PRIORITY.items():

            if self._term_in_text(
                city,
                location,
            ):
                return score

        # Explicit remote.

        if self._contains_any(
            location,
            self.REMOTE_TERMS,
        ):
            return 16

        if self._contains_any(
            workplace_type,
            self.REMOTE_TERMS,
        ):
            return 16

        if self._contains_any(
            text,
            self.REMOTE_TERMS,
        ):
            return 14

        # Finland.

        if self._contains_any(
            location,
            self.FINLAND_TERMS,
        ):
            return 10

        return 0

    # =========================================================
    # Seniority
    # =========================================================

    def _detect_seniority(
        self,
        title,
        text,
    ):
        """
        Title has priority.

        Description-level seniority is only used when the
        title itself does not contain a seniority signal.
        """

        title = self._clean_text(
            title
        )

        text = self._clean_text(
            text
        )

        ordered_levels = [
            "director",
            "manager",
            "lead",
            "architect",
            "senior",
            "junior",
            "intern",
        ]

        # -----------------------------------------------------
        # First: title
        # -----------------------------------------------------

        for level in ordered_levels:

            for term in self.SENIORITY_TERMS[level]:

                if self._term_in_text(
                    term,
                    title,
                ):
                    return level

        # -----------------------------------------------------
        # Second: description
        # -----------------------------------------------------

        description_levels = [
            "director",
            "manager",
            "lead",
            "architect",
            "senior",
        ]

        for level in description_levels:

            for term in self.SENIORITY_TERMS[level]:

                if self._term_in_text(
                    term,
                    text,
                ):
                    return level

        return "unspecified"

    # =========================================================
    # Required experience extraction
    # =========================================================

    def _extract_required_experience(
        self,
        text,
    ):
        text = self._clean_text(
            text
        )

        patterns = [
            r"(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience",
            r"minimum\s+of\s+(\d+)\s+years?",
            r"at\s+least\s+(\d+)\s+years?",
            r"(\d+)\s*-\s*\d+\s+years?\s+(?:of\s+)?experience",
            r"(\d+)\s*\+\s*years?",
        ]

        matches = []

        for pattern in patterns:

            found = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            for value in found:

                try:
                    matches.append(
                        int(value)
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        if not matches:
            return None

        return max(matches)

    # =========================================================
    # Experience requirement penalty
    # =========================================================

    def _experience_requirement_penalty(
        self,
        years,
    ):
        if years is None:
            return 0

        if years >= 7:
            return 20

        if years >= 5:
            return 15

        if years >= 4:
            return 11

        if years >= 3:
            return 7

        if years >= 2:
            return 3

        return 0

    # =========================================================
    # Single-job convenience method
    # =========================================================

    def match_job(
        self,
        job,
        profile,
    ):
        ranked = self.rank_jobs(
            [job],
            profile,
        )

        if not ranked:
            return None

        return ranked[0]