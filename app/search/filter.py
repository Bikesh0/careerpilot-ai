class JobFilter:
    """
    CareerPilot AI job relevance filter.

    Purpose:
    - Remove clearly unrelated jobs.
    - Keep cybersecurity, information security, SOC, IAM,
      cloud, infrastructure, networking, Linux, IT support,
      DevOps and related technical roles.
    - Do NOT make the filter responsible for deciding whether
      a job is a strong match. That is handled by JobMatcher.
    """

    ALLOWED_KEYWORDS = [
        # ---------------------------------------------------------
        # Cybersecurity
        # ---------------------------------------------------------
        "cybersecurity",
        "cyber security",
        "cyber-security",
        "information security",
        "infosec",
        "security analyst",
        "security specialist",
        "security engineer",
        "security administrator",
        "security operations",
        "security operations center",
        "soc analyst",
        "soc",
        "siem",
        "splunk",
        "incident response",
        "incident management",
        "threat detection",
        "threat intelligence",
        "threat hunting",
        "vulnerability",
        "vulnerability management",
        "penetration testing",
        "penetration tester",
        "ethical hacking",
        "application security",
        "network security",
        "cloud security",
        "endpoint security",
        "detection and response",
        "security monitoring",
        "security operations",

        # ---------------------------------------------------------
        # IAM / Identity
        # ---------------------------------------------------------
        "iam",
        "identity and access management",
        "identity management",
        "access management",
        "privileged access management",
        "pam",
        "identity",
        "authentication",
        "authorization",
        "oauth",
        "access control",

        # ---------------------------------------------------------
        # Networking
        # ---------------------------------------------------------
        "network engineer",
        "network administrator",
        "network administrator",
        "networking",
        "network",
        "tcp/ip",
        "routing",
        "switching",
        "vpn",
        "firewall",
        "fortinet",
        "cisco",
        "ccna",
        "ids",
        "ips",
        "intrusion detection",
        "intrusion prevention",

        # ---------------------------------------------------------
        # Linux / Systems / Infrastructure
        # ---------------------------------------------------------
        "linux",
        "linux administrator",
        "linux system administrator",
        "system administrator",
        "systems administrator",
        "system engineer",
        "systems engineer",
        "infrastructure engineer",
        "infrastructure",
        "server administrator",
        "server",
        "virtualization",
        "vmware",
        "zfs",
        "iscsi",

        # ---------------------------------------------------------
        # Cloud
        # ---------------------------------------------------------
        "cloud",
        "cloud engineer",
        "cloud support",
        "cloud administrator",
        "cloud infrastructure",
        "cloud operations",
        "aws",
        "amazon web services",
        "azure",
        "microsoft azure",
        "google cloud",
        "gcp",

        # ---------------------------------------------------------
        # DevOps / Platform
        # ---------------------------------------------------------
        "devops",
        "devops engineer",
        "platform engineer",
        "site reliability",
        "sre",
        "docker",
        "kubernetes",
        "container",
        "containers",
        "ci/cd",
        "continuous integration",
        "continuous deployment",
        "git",
        "terraform",
        "ansible",

        # ---------------------------------------------------------
        # IT Support
        # ---------------------------------------------------------
        "it support",
        "technical support",
        "technical support engineer",
        "it specialist",
        "it administrator",
        "helpdesk",
        "help desk",
        "service desk",
        "service desk analyst",
        "support engineer",
        "desktop support",
        "systems support",

        # ---------------------------------------------------------
        # General technical roles
        # ---------------------------------------------------------
        "it",
        "information technology",
        "technical",
        "infrastructure",
        "operations",
    ]

    BLOCKED_KEYWORDS = [
        # Clearly unrelated career areas
        "marketing",
        "sales representative",
        "sales manager",
        "sales director",
        "account executive",
        "business development",
        "finance",
        "financial analyst",
        "accounting",
        "accountant",
        "human resources",
        "hr manager",
        "recruiter",
        "recruitment",
        "talent acquisition",
        "graphic designer",
        "graphic design",
        "ux designer",
        "ui designer",
        "social media manager",
        "social media specialist",

        # Clearly non-technical roles
        "waiter",
        "waitress",
        "restaurant manager",
        "chef",
        "cook",
        "cleaner",
        "cleaning",
        "nurse",
        "doctor",
        "teacher",
        "kindergarten teacher",
        "salesperson",
    ]

    def get_text(self, job):
        """
        Safely combine title, description and other useful fields.
        Works with both dictionaries and Job objects.
        """

        if isinstance(job, dict):
            title = job.get("title", "") or ""
            description = job.get("description", "") or ""
            company = job.get("company", "") or ""
            location = job.get("location", "") or ""

        else:
            title = getattr(job, "title", "") or ""
            description = getattr(job, "description", "") or ""
            company = getattr(job, "company", "") or ""
            location = getattr(job, "location", "") or ""

        return (
            f"{title} "
            f"{description} "
            f"{company} "
            f"{location}"
        ).lower()

    def get_title(self, job):
        """
        Safely return the job title.
        """

        if isinstance(job, dict):
            return (job.get("title", "") or "").strip()

        return (
            getattr(job, "title", "") or ""
        ).strip()

    def remove_duplicates(self, jobs):
        """
        Remove duplicate jobs primarily by title + company.

        This is better than title-only deduplication because
        different companies can legitimately have the same title.
        """

        unique = []
        seen = set()

        for job in jobs:

            title = self.get_title(job)

            if isinstance(job, dict):
                company = (
                    job.get("company", "") or ""
                ).strip()
            else:
                company = (
                    getattr(job, "company", "") or ""
                ).strip()

            key = (
                title.lower(),
                company.lower(),
            )

            if key not in seen:
                seen.add(key)
                unique.append(job)

        return unique

    def cybersecurity_only(self, jobs):
        """
        Keep jobs that have a meaningful technical/security signal.

        Important:
        This is a BROAD relevance filter, not the final matcher.

        A job does not need to literally contain the word
        'cybersecurity' to survive this stage.

        Examples:
        - SOC Analyst -> keep
        - Information Security Specialist -> keep
        - PAM Specialist -> keep
        - Linux System Administrator -> keep
        - Cloud Support Engineer -> keep
        - Network Engineer -> keep
        - Technical Support -> keep

        The JobMatcher later determines the actual match percentage.
        """

        filtered = []

        for job in jobs:

            text = self.get_text(job)

            if not text.strip():
                continue

            # -----------------------------------------------------
            # First remove clearly unrelated jobs.
            # -----------------------------------------------------

            blocked = any(
                keyword in text
                for keyword in self.BLOCKED_KEYWORDS
            )

            if blocked:
                continue

            # -----------------------------------------------------
            # Keep jobs containing at least one technical signal.
            # -----------------------------------------------------

            allowed = any(
                keyword in text
                for keyword in self.ALLOWED_KEYWORDS
            )

            if allowed:
                filtered.append(job)

        return filtered