"""
Job-specific skill-gap analysis and recommendation engine.

Deliberately makes zero LLM/Ollama calls. Two reasons, both consistent
with this project's existing design boundary (see docs/AI.md - "Not used
for matching, ranking, deduplication, filtering, or search"):

1. A skill gap needs to be explainable and reproducible ("why does this
   say I'm missing Terraform") the same way matching/ranking scores do -
   an LLM call would make that non-deterministic.
2. Recommending a certification or course is exactly the kind of claim
   that must not be hallucinated. Keeping this feature to a small,
   hand-curated, verifiable catalog (real, well-known certifications and
   providers) means every recommendation shown is "verified" by
   construction - there is no AI-generated content to separately flag
   because none is generated. If this is ever extended with LLM-written
   narrative text, that content must be clearly labeled as AI-generated
   and kept separate from this catalog, not blended into it.

Two genuinely separate things are computed here, and both matter:

- **Job requirement coverage**: does the job ask for a skill (required or
  nice-to-have) that isn't demonstrated anywhere in the profile at all?
  This is the actual "skill gap" - distinct from `MatchResult.missing_skills`
  in both matchers (V1's `app/ai/matcher.py`, V2's
  `app/search/v2/matching/`), which means "profile skills this job's text
  doesn't happen to repeat" - the inverse relationship. See
  `docs/MATCHING_AND_RANKING.md` for why that distinction matters and was
  never silently conflated here.
- **CV evidence quality**: for a skill the job wants that the profile does
  claim, is it backed by an experience entry, or only present in the bare
  skills list (or vice versa)? This never invents evidence - it only
  points out where the *existing* profile data is thin.
"""

import re


# =============================================================
# Word-boundary matching (self-contained, mirrors the equivalent
# helper in app/search/v2/matching/signals.py - not imported from there
# to keep this feature decoupled from V2's search-pipeline internals,
# the same precedent app/ai/matcher.py already sets with its own
# independent _term_in_text).
# =============================================================

def _normalize(value):
    value = str(value or "").strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[/_-]+", " ", value)

    # Periods are deliberately NOT kept (unlike the otherwise-similar
    # normalizer in app/search/v2/matching/signals.py): this module
    # tokenizes whole natural-language sentences pulled straight from
    # job postings, where a skill name is very often the last word
    # before a full stop ("...experience with Terraform."). Keeping the
    # period would glue it onto the token ("terraform.") and silently
    # break the exact-token match against the alias ("terraform").
    value = re.sub(r"[^a-z0-9+# ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokenize(value):
    normalized = _normalize(value)
    return normalized.split() if normalized else []


def _contains_term(text, term):
    text_tokens = _tokenize(text)
    term_tokens = _tokenize(term)

    if not text_tokens or not term_tokens:
        return False

    width = len(term_tokens)

    return any(
        text_tokens[i:i + width] == term_tokens
        for i in range(len(text_tokens) - width + 1)
    )


def _contains_any(text, terms):
    return any(_contains_term(text, term) for term in terms)


# =============================================================
# Required vs. nice-to-have heuristic
#
# Job postings rarely have clean, machine-readable "Requirements" /
# "Nice to have" sections once reduced to plain text. Instead of relying
# on section headers, each sentence/line is checked independently for a
# hedging phrase ("nice to have", "a plus", "preferred", ...). A skill
# mentioned in a hedged sentence is nice-to-have; anywhere else, it's
# treated as required. This is a heuristic, not a parser - documented as
# a known limitation in docs/MATCHING_AND_RANKING.md.
# =============================================================

_NICE_TO_HAVE_MARKERS = [
    "nice to have",
    "nice-to-have",
    "preferred",
    "is a plus",
    "a plus",
    "bonus",
    "advantageous",
    "desirable",
    "good to have",
    "would be a plus",
    "not required",
    "optional",
    "beneficial",
]


def _split_chunks(text):
    text = str(text or "")
    chunks = re.split(r"[\n\r]+|(?<=[.!?])\s+", text)
    return [chunk for chunk in chunks if chunk.strip()]


def _chunk_is_nice_to_have(chunk):
    lowered = chunk.lower()
    return any(marker in lowered for marker in _NICE_TO_HAVE_MARKERS)


# =============================================================
# Skill catalog
#
# One entry per recognized skill: detection aliases, plus a small,
# hand-curated set of real certifications/courses/projects. Every named
# certification/course/provider below is a real, well-known, long-
# standing one - not invented, and not claimed to teach anything beyond
# its actual, publicly documented scope. `effort_days` is a rough,
# deliberately conservative (min, max) estimate used only to order
# recommendations from quickest to most involved - not a promise.
#
# This is a curated taxonomy, not job-text extraction: a skill the job
# posting mentions that isn't one of these keys is invisible to this
# feature. Scoped this way deliberately - see NEXT_TASKS.md's prior
# "Priority 3" note on why a curated taxonomy is the safer default over
# a per-job LLM call.
# =============================================================

SKILL_CATALOG = {
    "linux": {
        "display": "Linux",
        "aliases": ["linux", "ubuntu", "red hat", "rhel", "debian"],
        "certifications": [
            {
                "name": "CompTIA Linux+",
                "why": (
                    "Vendor-neutral certification validating practical "
                    "Linux administration across distributions."
                ),
            },
            {
                "name": "Red Hat Certified System Administrator (RHCSA)",
                "why": (
                    "Hands-on, performance-based exam focused on Red Hat "
                    "Enterprise Linux system administration."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Linux Foundation",
                "name": "Introduction to Linux (LFS101, free)",
            },
        ],
        "projects": [
            {
                "title": "Home lab server",
                "description": (
                    "Set up and harden a Linux server (SSH key auth, "
                    "firewall rules, fail2ban, automatic updates) and "
                    "document the configuration in a public GitHub repo."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "networking": {
        "display": "Networking",
        "aliases": [
            "networking", "tcp/ip", "routing", "switching",
            "network administration",
        ],
        "certifications": [
            {
                "name": "CCNA (Cisco Certified Network Associate)",
                "why": (
                    "Industry-standard certification covering routing, "
                    "switching, and IP networking fundamentals."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Cisco Networking Academy",
                "name": (
                    "Networking Basics / CCNA course materials "
                    "(free enrollment)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Home network segmentation",
                "description": (
                    "Configure VLANs and routing between them on a home "
                    "router/switch (or in GNS3/Packet Tracer) and "
                    "document the topology."
                ),
            },
        ],
        "effort_days": (7, 14),
    },
    "python": {
        "display": "Python",
        "aliases": ["python"],
        "certifications": [
            {
                "name": "PCEP - Certified Entry-Level Python Programmer",
                "why": (
                    "Entry-level, vendor-neutral certification confirming "
                    "basic Python proficiency for scripting/automation."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Python Software Foundation",
                "name": "Official Python Tutorial (docs.python.org, free)",
            },
        ],
        "projects": [
            {
                "title": "Log-parsing automation script",
                "description": (
                    "Write a Python script that parses a sample log "
                    "file, flags suspicious entries, and outputs a "
                    "summary report."
                ),
            },
        ],
        "effort_days": (3, 7),
    },
    "docker": {
        "display": "Docker",
        "aliases": ["docker", "containerization", "containers"],
        "certifications": [
            {
                "name": "Docker Certified Associate (DCA)",
                "why": (
                    "Validates practical container build/deploy/"
                    "troubleshoot skills."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Docker",
                "name": "Docker official 'Get Started' guide (docs.docker.com, free)",
            },
        ],
        "projects": [
            {
                "title": "Containerize an existing app",
                "description": (
                    "Write a Dockerfile and docker-compose setup for a "
                    "small existing project and publish the build steps "
                    "in a README."
                ),
            },
        ],
        "effort_days": (3, 5),
    },
    "kubernetes": {
        "display": "Kubernetes",
        "aliases": ["kubernetes", "k8s"],
        "certifications": [
            {
                "name": "Certified Kubernetes Administrator (CKA)",
                "why": (
                    "The recognized hands-on certification for "
                    "Kubernetes cluster administration."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Kubernetes.io",
                "name": (
                    "Official 'Learn Kubernetes Basics' interactive "
                    "tutorial (free)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Local cluster deployment",
                "description": (
                    "Deploy a small multi-service app to a local cluster "
                    "(minikube or kind), configure a Service and "
                    "Ingress, and document the steps."
                ),
            },
        ],
        "effort_days": (7, 14),
    },
    "aws": {
        "display": "AWS",
        "aliases": ["aws", "amazon web services"],
        "certifications": [
            {
                "name": "AWS Certified Cloud Practitioner",
                "why": (
                    "Foundational, vendor-issued certification "
                    "demonstrating core AWS knowledge."
                ),
            },
        ],
        "courses": [
            {
                "provider": "AWS Skill Builder",
                "name": "Cloud Practitioner Essentials (free)",
            },
        ],
        "projects": [
            {
                "title": "Static site on AWS",
                "description": (
                    "Host a small static site using S3 + CloudFront, "
                    "and write up the architecture and IAM permissions "
                    "used."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "azure": {
        "display": "Azure",
        "aliases": ["azure", "microsoft azure"],
        "certifications": [
            {
                "name": "Microsoft Certified: Azure Fundamentals (AZ-900)",
                "why": "Microsoft's own foundational certification for Azure.",
            },
        ],
        "courses": [
            {
                "provider": "Microsoft Learn",
                "name": "AZ-900 Azure Fundamentals learning path (free)",
            },
        ],
        "projects": [
            {
                "title": "Azure resource group lab",
                "description": (
                    "Deploy a small VM + storage account in a free-tier "
                    "Azure subscription and document the resource group "
                    "and network setup."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "google cloud": {
        "display": "Google Cloud",
        "aliases": ["gcp", "google cloud", "google cloud platform"],
        "certifications": [
            {
                "name": "Google Cloud Associate Cloud Engineer",
                "why": (
                    "Google's associate-level certification validating "
                    "core GCP deployment/management skills."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Google Cloud Skills Boost",
                "name": (
                    "Google Cloud Fundamentals: Core Infrastructure "
                    "(free tier available)"
                ),
            },
        ],
        "projects": [
            {
                "title": "GCP compute lab",
                "description": (
                    "Deploy a small Compute Engine instance and Cloud "
                    "Storage bucket within the GCP free tier and "
                    "document the IAM roles used."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "terraform": {
        "display": "Terraform",
        "aliases": ["terraform", "infrastructure as code", "iac"],
        "certifications": [
            {
                "name": "HashiCorp Certified: Terraform Associate",
                "why": "The standard vendor certification for Terraform.",
            },
        ],
        "courses": [
            {
                "provider": "HashiCorp Developer",
                "name": (
                    "Terraform 'Get Started' tutorials "
                    "(developer.hashicorp.com, free)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Terraform-provisioned lab environment",
                "description": (
                    "Provision a small cloud environment (VPC + one "
                    "compute instance + security group) entirely with "
                    "Terraform and publish the code on GitHub."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "ansible": {
        "display": "Ansible",
        "aliases": ["ansible"],
        "certifications": [
            {
                "name": "Red Hat Certified Specialist in Ansible Automation",
                "why": (
                    "Vendor certification validating practical "
                    "configuration-management/automation skills with "
                    "Ansible."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Ansible/Red Hat",
                "name": (
                    "Ansible official 'Getting Started' guide "
                    "(docs.ansible.com, free)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Server-config automation playbook",
                "description": (
                    "Write an Ansible playbook that installs and "
                    "hardens a base package set across two or more "
                    "test VMs."
                ),
            },
        ],
        "effort_days": (3, 7),
    },
    "siem": {
        "display": "SIEM",
        "aliases": ["siem", "security information and event management"],
        "certifications": [
            {
                "name": "Splunk Core Certified User",
                "why": (
                    "Widely recognized starting certification for "
                    "SIEM/log-analysis work."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Splunk",
                "name": "Splunk Fundamentals 1 (free, self-paced)",
            },
        ],
        "projects": [
            {
                "title": "SIEM dashboard from lab logs",
                "description": (
                    "Ingest sample log data into a free SIEM tool "
                    "(e.g. Splunk Free or the Elastic Stack) and build "
                    "a dashboard flagging failed-login spikes."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "splunk": {
        "display": "Splunk",
        "aliases": ["splunk"],
        "certifications": [
            {
                "name": "Splunk Core Certified User",
                "why": "Splunk's own entry-level certification.",
            },
        ],
        "courses": [
            {
                "provider": "Splunk",
                "name": "Splunk Fundamentals 1 (free, self-paced)",
            },
        ],
        "projects": [
            {
                "title": "Splunk log ingestion lab",
                "description": (
                    "Install Splunk Free, ingest a sample dataset, and "
                    "build searches/dashboards summarizing key events."
                ),
            },
        ],
        "effort_days": (3, 7),
    },
    "microsoft sentinel": {
        "display": "Microsoft Sentinel",
        "aliases": ["sentinel", "microsoft sentinel", "azure sentinel"],
        "certifications": [
            {
                "name": (
                    "Microsoft Certified: Security Operations Analyst "
                    "Associate (SC-200)"
                ),
                "why": (
                    "Microsoft's own certification for SOC analysts "
                    "using Microsoft Sentinel/Defender."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Microsoft Learn",
                "name": "SC-200 learning path (free)",
            },
        ],
        "projects": [
            {
                "title": "Sentinel trial workspace",
                "description": (
                    "Stand up a Sentinel workspace in an Azure free "
                    "trial, connect a sample data source, and build "
                    "one detection rule."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "qradar": {
        "display": "QRadar",
        "aliases": ["qradar"],
        "certifications": [
            {
                "name": "IBM Certified Associate Analyst - QRadar SIEM",
                "why": "IBM's own associate-level QRadar certification.",
            },
        ],
        "courses": [
            {
                "provider": "IBM Skills Network",
                "name": (
                    "IBM QRadar SIEM Foundations (free courses "
                    "available)"
                ),
            },
        ],
        "projects": [
            {
                "title": "QRadar community edition lab",
                "description": (
                    "Install QRadar Community Edition in a lab VM, "
                    "ingest sample events, and document one "
                    "investigated offense."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "elastic stack": {
        "display": "Elastic Stack (ELK)",
        "aliases": ["elastic", "elk stack", "elasticsearch", "kibana"],
        "certifications": [
            {
                "name": "Elastic Certified Analyst",
                "why": (
                    "Elastic's own certification for using the Elastic "
                    "Stack for security/data analysis."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Elastic",
                "name": (
                    "Elastic official 'Getting Started' guide "
                    "(elastic.co, free)"
                ),
            },
        ],
        "projects": [
            {
                "title": "ELK log pipeline",
                "description": (
                    "Stand up Elasticsearch + Kibana locally (Docker), "
                    "ship sample logs with Filebeat, and build a Kibana "
                    "dashboard."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "incident response": {
        "display": "Incident Response",
        "aliases": ["incident response", "incident handling"],
        "certifications": [
            {
                "name": "GIAC Certified Incident Handler (GCIH)",
                "why": (
                    "Widely recognized certification specifically "
                    "focused on incident-handling methodology."
                ),
            },
        ],
        "courses": [
            {
                "provider": "TryHackMe",
                "name": (
                    "SOC Level 1 learning path (includes incident-"
                    "response modules, free tier available)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Documented incident-response runbook",
                "description": (
                    "Write a short incident-response runbook "
                    "(detect -> contain -> eradicate -> recover) for a "
                    "specific scenario, e.g. a phishing compromise."
                ),
            },
        ],
        "effort_days": (5, 14),
    },
    "penetration testing": {
        "display": "Penetration Testing",
        "aliases": [
            "penetration testing", "pentesting", "pen testing",
            "ethical hacking",
        ],
        "certifications": [
            {
                "name": "Certified Ethical Hacker (CEH)",
                "why": (
                    "Widely recognized entry certification in "
                    "offensive security."
                ),
            },
            {
                "name": (
                    "eLearnSecurity/INE eJPT (Junior Penetration Tester)"
                ),
                "why": (
                    "A hands-on, exam-based junior pentesting "
                    "certification well suited to an early-career "
                    "profile."
                ),
            },
        ],
        "courses": [
            {
                "provider": "TryHackMe",
                "name": (
                    "'Jr Penetration Tester' learning path "
                    "(free tier available)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Documented lab pentest",
                "description": (
                    "Complete a legal practice target (e.g. a "
                    "TryHackMe or HackTheBox machine) and write up the "
                    "methodology and findings as a portfolio report."
                ),
            },
        ],
        "effort_days": (7, 14),
    },
    "vulnerability management": {
        "display": "Vulnerability Management",
        "aliases": [
            "vulnerability management", "vulnerability assessment",
            "vulnerability scanning",
        ],
        "certifications": [
            {
                "name": "CompTIA Security+",
                "why": (
                    "Covers vulnerability management fundamentals as "
                    "part of its broad, widely-required security "
                    "baseline."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Tenable / Nessus",
                "name": "Nessus Essentials (free scanner) getting-started guide",
            },
        ],
        "projects": [
            {
                "title": "Home-lab vulnerability scan",
                "description": (
                    "Run a free vulnerability scanner (e.g. Nessus "
                    "Essentials or OpenVAS) against a lab VM, and write "
                    "a short remediation report for the findings."
                ),
            },
        ],
        "effort_days": (3, 7),
    },
    "firewall": {
        "display": "Firewall",
        "aliases": ["firewall", "firewalls"],
        "certifications": [
            {
                "name": "CompTIA Security+",
                "why": (
                    "Covers firewall concepts and configuration as "
                    "part of its core security curriculum."
                ),
            },
        ],
        "courses": [
            {
                "provider": "pfSense / OPNsense",
                "name": (
                    "Official documentation and getting-started guides "
                    "(free, open source)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Home-lab firewall build",
                "description": (
                    "Set up pfSense or OPNsense in a home lab (or a "
                    "VM), configure rule-based traffic filtering, and "
                    "document the rule set."
                ),
            },
        ],
        "effort_days": (3, 7),
    },
    "ids/ips": {
        "display": "IDS/IPS",
        "aliases": ["ids", "ips", "intrusion detection", "intrusion prevention"],
        "certifications": [
            {
                "name": "GIAC Certified Intrusion Analyst (GCIA)",
                "why": (
                    "Focused specifically on network intrusion "
                    "detection/analysis."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Snort/Suricata",
                "name": (
                    "Official documentation and rule-writing guides "
                    "(free, open source)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Home-lab IDS deployment",
                "description": (
                    "Deploy Snort or Suricata in a lab environment, "
                    "write a couple of custom detection rules, and "
                    "document what they catch."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "iam": {
        "display": "IAM",
        "aliases": ["iam", "identity and access management"],
        "certifications": [
            {
                "name": "Certified Identity and Access Manager (CIAM)",
                "why": (
                    "A certification focused specifically on identity "
                    "and access management practices."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Microsoft Learn",
                "name": (
                    "'Implement identity management solutions' "
                    "learning path (free)"
                ),
            },
        ],
        "projects": [
            {
                "title": "IAM policy walkthrough",
                "description": (
                    "Design and document a least-privilege IAM "
                    "role/policy set for a small sample AWS or Azure "
                    "environment."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "active directory": {
        "display": "Active Directory",
        "aliases": ["active directory"],
        "certifications": [
            {
                "name": (
                    "Microsoft Certified: Identity and Access "
                    "Administrator Associate (SC-300)"
                ),
                "why": (
                    "Microsoft's certification for identity/access "
                    "administration, including Active Directory-based "
                    "environments."
                ),
            },
        ],
        "courses": [
            {
                "provider": "Microsoft Learn",
                "name": "SC-300 learning path (free)",
            },
        ],
        "projects": [
            {
                "title": "AD lab environment",
                "description": (
                    "Set up a small Active Directory domain in a VM "
                    "lab, create OUs/group policies, and document the "
                    "structure."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "vpn": {
        "display": "VPN",
        "aliases": ["vpn", "virtual private network"],
        "certifications": [],
        "courses": [
            {
                "provider": "OpenVPN / WireGuard",
                "name": (
                    "Official documentation and setup guides "
                    "(free, open source)"
                ),
            },
        ],
        "projects": [
            {
                "title": "Self-hosted VPN",
                "description": (
                    "Set up a WireGuard or OpenVPN server on a home "
                    "lab/VPS and document the configuration and client "
                    "setup."
                ),
            },
        ],
        "effort_days": (2, 5),
    },
    "ci/cd": {
        "display": "CI/CD",
        "aliases": [
            "ci/cd", "continuous integration", "continuous deployment",
            "continuous delivery",
        ],
        "certifications": [
            {
                "name": "GitLab Certified CI/CD Associate",
                "why": "Vendor certification specifically on CI/CD pipeline design.",
            },
        ],
        "courses": [
            {
                "provider": "GitHub",
                "name": "GitHub Actions official documentation and quickstart (free)",
            },
        ],
        "projects": [
            {
                "title": "CI pipeline for an existing project",
                "description": (
                    "Add a GitHub Actions workflow to an existing repo "
                    "that runs tests/lints automatically on every push."
                ),
            },
        ],
        "effort_days": (2, 5),
    },
    "git": {
        "display": "Git",
        "aliases": ["git", "github", "gitlab"],
        "certifications": [],
        "courses": [
            {
                "provider": "Git",
                "name": "Official Git documentation / Pro Git book (git-scm.com, free)",
            },
        ],
        "projects": [
            {
                "title": "Public portfolio repo",
                "description": (
                    "Move an existing project onto GitHub with a clear "
                    "README, commit history, and issue tracker."
                ),
            },
        ],
        "effort_days": (1, 3),
    },
    "powershell": {
        "display": "PowerShell",
        "aliases": ["powershell"],
        "certifications": [],
        "courses": [
            {
                "provider": "Microsoft Learn",
                "name": "'PowerShell fundamentals' learning path (free)",
            },
        ],
        "projects": [
            {
                "title": "System-audit script",
                "description": (
                    "Write a PowerShell script that audits local user "
                    "accounts and installed services on a Windows VM "
                    "and outputs a report."
                ),
            },
        ],
        "effort_days": (3, 7),
    },
    "bash scripting": {
        "display": "Bash Scripting",
        "aliases": ["bash", "shell scripting"],
        "certifications": [],
        "courses": [
            {
                "provider": "Linux Foundation",
                "name": (
                    "Introduction to Linux (LFS101, free) - includes "
                    "shell scripting basics"
                ),
            },
        ],
        "projects": [
            {
                "title": "Log-rotation/monitoring script",
                "description": (
                    "Write a Bash script that monitors disk usage or "
                    "rotates logs on a lab server, with cron "
                    "scheduling."
                ),
            },
        ],
        "effort_days": (2, 5),
    },
    "cloud security": {
        "display": "Cloud Security",
        "aliases": ["cloud security"],
        "certifications": [
            {
                "name": "CompTIA Cloud+",
                "why": (
                    "Vendor-neutral certification covering cloud "
                    "security fundamentals across providers."
                ),
            },
            {
                "name": "AWS Certified Security - Specialty",
                "why": (
                    "A deeper, AWS-specific security certification for "
                    "candidates already working with AWS."
                ),
            },
        ],
        "courses": [
            {
                "provider": "AWS Skill Builder",
                "name": "'AWS Cloud Security Fundamentals' course (free)",
            },
        ],
        "projects": [
            {
                "title": "Cloud security baseline review",
                "description": (
                    "Review a free-tier AWS or Azure account against a "
                    "public security baseline (e.g. CIS Benchmarks) "
                    "and document findings."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "compliance and governance": {
        "display": "Compliance & Governance",
        "aliases": [
            "gdpr", "iso 27001", "compliance",
            "governance risk and compliance", "grc",
        ],
        "certifications": [
            {
                "name": "ISO/IEC 27001 Foundation",
                "why": (
                    "Entry-level certification on the ISO 27001 "
                    "information-security management standard."
                ),
            },
        ],
        "courses": [
            {
                "provider": "ENISA / official EU GDPR portal",
                "name": "GDPR overview materials (free, official EU resource)",
            },
        ],
        "projects": [
            {
                "title": "Mini compliance gap-analysis",
                "description": (
                    "Pick a small sample organization/scenario and "
                    "write a short gap-analysis document against ISO "
                    "27001 Annex A controls."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "digital forensics": {
        "display": "Digital Forensics",
        "aliases": ["digital forensics", "forensics"],
        "certifications": [
            {
                "name": "GIAC Certified Forensic Examiner (GCFE)",
                "why": (
                    "Recognized certification specifically focused on "
                    "digital forensics methodology."
                ),
            },
        ],
        "courses": [
            {
                "provider": "SANS / DFIR community",
                "name": (
                    "Publicly available DFIR training materials and "
                    "SANS DFIR free webcasts"
                ),
            },
        ],
        "projects": [
            {
                "title": "Disk-image analysis writeup",
                "description": (
                    "Analyze a publicly available forensic practice "
                    "image (e.g. from DFIR.training) with an "
                    "open-source tool like Autopsy and document the "
                    "findings."
                ),
            },
        ],
        "effort_days": (5, 10),
    },
    "soc operations": {
        "display": "SOC Operations",
        "aliases": ["security operations center", "soc"],
        "certifications": [
            {
                "name": "CompTIA Security+",
                "why": (
                    "Broad security baseline certification commonly "
                    "requested for SOC analyst roles."
                ),
            },
        ],
        "courses": [
            {
                "provider": "TryHackMe",
                "name": "SOC Level 1 learning path (free tier available)",
            },
        ],
        "projects": [
            {
                "title": "SOC triage documentation",
                "description": (
                    "Work through a free SOC-analyst simulation (e.g. "
                    "TryHackMe SOC Level 1 rooms) and document the "
                    "triage/investigation steps taken."
                ),
            },
        ],
        "effort_days": (5, 14),
    },
}


# =============================================================
# Profile text extraction
# =============================================================

def _job_text(job):
    parts = [
        getattr(job, "title", "") or "",
        getattr(job, "description", "") or "",
    ]
    return " ".join(str(part) for part in parts)


def _profile_skills_text(profile):
    skills = profile.get("skills", []) if profile else []
    return " ".join(str(skill) for skill in skills or [])


def _profile_experience_text(profile):
    experience = profile.get("experience", []) if profile else []
    parts = []

    for item in experience or []:
        if isinstance(item, dict):
            parts.extend(str(value) for value in item.values() if value)
        else:
            parts.append(str(item))

    return " ".join(parts)


def _profile_certifications_text(profile):
    certifications = profile.get("certifications", []) if profile else []
    return " ".join(str(cert) for cert in certifications or [])


def _candidate_text(profile):
    return " ".join([
        _profile_skills_text(profile),
        _profile_experience_text(profile),
        _profile_certifications_text(profile),
        str((profile or {}).get("summary", "") or ""),
    ])


# =============================================================
# Main entry point
# =============================================================

def analyze_skill_gap(profile, job):
    """
    Compare a single job's requirements against the candidate profile.

    Returns a dict shaped for direct template rendering:

    {
        "job_title": str,
        "company": str,
        "required": [ {skill, priority, status, ...}, ... ],
        "nice_to_have": [ ... ],
        "priority_actions": [ ... ],  # missing skills, required first,
                                       # quickest effort first
        "cv_improvements": [str, ...],
        "summary": {...},
    }

    Each entry in "required"/"nice_to_have" is either:
    - {"skill", "priority", "status": "matched", "cv_note": str | absent}
    - {"skill", "priority", "status": "missing", "recommendation": {...}}
    """

    profile = profile or {}
    job_chunks = _split_chunks(_job_text(job))

    required_skills = []
    nice_to_have_skills = []

    for key, entry in SKILL_CATALOG.items():
        aliases = entry["aliases"]

        required_hit = any(
            _contains_any(chunk, aliases) and not _chunk_is_nice_to_have(chunk)
            for chunk in job_chunks
        )

        if required_hit:
            required_skills.append(key)
            continue

        nice_hit = any(
            _contains_any(chunk, aliases) and _chunk_is_nice_to_have(chunk)
            for chunk in job_chunks
        )

        if nice_hit:
            nice_to_have_skills.append(key)

    candidate_text = _candidate_text(profile)
    experience_text = _profile_experience_text(profile)
    skills_text = _profile_skills_text(profile)

    def build_entry(key, priority):
        entry = SKILL_CATALOG[key]
        aliases = entry["aliases"]
        has_skill = _contains_any(candidate_text, aliases)

        result = {
            "key": key,
            "skill": entry["display"],
            "priority": priority,
            "status": "matched" if has_skill else "missing",
        }

        if has_skill:
            in_skills_list = _contains_any(skills_text, aliases)
            in_experience = _contains_any(experience_text, aliases)

            if in_skills_list and not in_experience:
                result["cv_note"] = (
                    f"{entry['display']} is listed in your skills, but no "
                    "experience entry demonstrates it - consider adding "
                    "a specific example if you have relevant experience."
                )
            elif in_experience and not in_skills_list:
                result["cv_note"] = (
                    f"{entry['display']} appears in your experience but "
                    "isn't listed in your skills - consider adding it "
                    "explicitly."
                )
        else:
            result["recommendation"] = {
                "certifications": entry.get("certifications", []),
                "courses": entry.get("courses", []),
                "projects": entry.get("projects", []),
                "effort_days": entry.get("effort_days"),
                "verified": True,
            }

        return result

    required_entries = [build_entry(key, "required") for key in required_skills]
    nice_entries = [
        build_entry(key, "nice_to_have") for key in nice_to_have_skills
    ]

    def effort_key(pair):
        key, _entry = pair
        effort = SKILL_CATALOG[key].get("effort_days") or (999, 999)
        return effort[0]

    missing_required_pairs = sorted(
        (
            pair for pair in zip(required_skills, required_entries)
            if pair[1]["status"] == "missing"
        ),
        key=effort_key,
    )
    missing_nice_pairs = sorted(
        (
            pair for pair in zip(nice_to_have_skills, nice_entries)
            if pair[1]["status"] == "missing"
        ),
        key=effort_key,
    )

    priority_actions = (
        [entry for _key, entry in missing_required_pairs]
        + [entry for _key, entry in missing_nice_pairs]
    )

    cv_improvements = [
        entry["cv_note"]
        for entry in required_entries + nice_entries
        if entry.get("cv_note")
    ]

    required_total = len(required_entries)
    required_matched = sum(
        1 for entry in required_entries if entry["status"] == "matched"
    )
    required_missing_count = required_total - required_matched
    nice_total = len(nice_entries)
    nice_matched = sum(
        1 for entry in nice_entries if entry["status"] == "matched"
    )

    summary = {
        "required_total": required_total,
        "required_matched": required_matched,
        "required_missing": required_missing_count,
        "nice_to_have_total": nice_total,
        "nice_to_have_matched": nice_matched,
        "nice_to_have_missing": nice_total - nice_matched,
        "readiness_percent": (
            round(required_matched / required_total * 100)
            if required_total else 100
        ),
        "no_requirements_detected": required_total == 0 and nice_total == 0,
    }

    # "Ready to apply" is deliberately conservative: only claimed when
    # there's at least one detected requirement AND every one of them is
    # covered. A posting with zero detected requirements never claims
    # readiness - "no_requirements_detected" already covers that case
    # honestly instead of implying false confidence.
    ready_to_apply = required_total > 0 and required_missing_count == 0

    one_next_action = _build_next_action(
        ready_to_apply, priority_actions, cv_improvements, nice_entries
    )

    match_score = _estimate_match_score_improvement(
        profile, job, required_entries
    )

    return {
        "job_title": getattr(job, "title", "") or "",
        "company": getattr(job, "company", "") or "",
        "required": required_entries,
        "nice_to_have": nice_entries,
        "priority_actions": priority_actions,
        "cv_improvements": cv_improvements,
        "summary": summary,
        "ready_to_apply": ready_to_apply,
        "one_next_action": one_next_action,
        "match_score": match_score,
    }


# =============================================================
# "One next best action" - the calm, focused alternative to a giant
# checklist. Only one action is surfaced as primary; everything else
# stays available in the full required/nice-to-have sections above for
# a user who wants to look further.
# =============================================================

def _concrete_step(entry):
    skill = entry["skill"]
    recommendation = entry.get("recommendation") or {}
    effort = recommendation.get("effort_days")
    effort_text = f" (~{effort[0]}-{effort[1]} days)" if effort else ""

    projects = recommendation.get("projects") or []
    courses = recommendation.get("courses") or []

    if projects:
        return f"{projects[0]['title']} for {skill}{effort_text}."

    if courses:
        return (
            f"{courses[0]['provider']} - {courses[0]['name']} "
            f"for {skill}{effort_text}."
        )

    return f"Build practical experience with {skill}{effort_text}."


def _build_next_action(ready_to_apply, priority_actions, cv_improvements, nice_entries):
    if ready_to_apply:
        return {
            "type": "apply",
            "message": (
                "Your profile already covers this role's required "
                "skills. Apply now."
            ),
        }

    missing_required_actions = [
        action for action in priority_actions
        if action["priority"] == "required"
    ]

    if missing_required_actions:
        entry = missing_required_actions[0]
        return {
            "type": "skill_gap",
            "message": f"Next best step: {_concrete_step(entry)}",
            "skill": entry["skill"],
        }

    if cv_improvements:
        return {
            "type": "cv_evidence",
            "message": f"Next best step: {cv_improvements[0]}",
        }

    missing_nice = [
        entry for entry in nice_entries if entry["status"] == "missing"
    ]

    if missing_nice:
        entry = missing_nice[0]
        return {
            "type": "optional",
            "message": (
                f"Optional: {entry['skill']} would strengthen this "
                "application further, but isn't required - apply "
                "without it if you're otherwise a good fit."
            ),
        }

    return {
        "type": "apply",
        "message": "No further gaps found for this posting - apply now.",
    }


# =============================================================
# Honest match-score-improvement estimate
#
# Re-runs V2's real, deterministic JobMatcher.score_job() - the exact
# same scoring code the dashboard uses when V2 is active - with the
# missing required skills hypothetically added to the profile. This is
# never a promise ("closing these gaps will get you to 90%"); it's a
# transparent re-computation the user can trust because it's the same
# formula, not a separate, unverifiable estimate.
# =============================================================

def _v2_score(profile_skills, job):
    from app.search.v2.matching.matcher import JobMatcher as V2JobMatcher

    matcher = V2JobMatcher(profile_skills=profile_skills)
    return matcher.score_job(job).score


def _estimate_match_score_improvement(profile, job, required_entries):
    missing_required_display = [
        entry["skill"]
        for entry in required_entries
        if entry["status"] == "missing"
    ]

    if not missing_required_display:
        return None

    base_skills = list((profile or {}).get("skills", []) or [])

    try:
        current = _v2_score(base_skills, job)
        potential = _v2_score(
            base_skills + missing_required_display, job
        )
    except Exception:
        # Scoring must never break the rest of the page - if it fails
        # for any reason, simply omit the projection rather than show a
        # broken or misleading number.
        return None

    delta = round(potential) - round(current)

    if delta < 1:
        return {
            "current": round(current),
            "potential": round(current),
            "meaningful": False,
            "note": (
                "Closing these gaps would not meaningfully change your "
                "match score for this specific posting."
            ),
        }

    return {
        "current": round(current),
        "potential": round(potential),
        "meaningful": True,
        "note": (
            "Estimated using CareerPilot's V2 skill/title/location/"
            "seniority scoring model, assuming every missing required "
            "skill above were added to your profile - not a guarantee, "
            "and may differ slightly from the score shown on the "
            "dashboard if V1 is currently the active matcher."
        ),
    }
