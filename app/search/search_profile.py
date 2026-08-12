class SearchProfile:

    def __init__(self):

        # Main target roles
        self.primary_titles = [
            "SOC Analyst",
            "Cybersecurity Analyst",
            "Information Security Specialist",
            "IT Security Specialist",
            "Junior Security Engineer",
            "Security Engineer"
        ]

        # Also acceptable
        self.secondary_titles = [
            "Cloud Security Engineer",
            "Systems Administrator",
            "System Administrator",
            "Cloud Support Engineer",
            "DevOps Security",
            "Security Operations",
            "Security Operations Analyst"
        ]

        # Relevant skills
        self.strong_skills = [
            "cybersecurity",
            "cyber security",
            "linux",
            "networking",
            "network security",
            "siem",
            "splunk",
            "incident response",
            "penetration testing",
            "firewall",
            "ids",
            "ips",
            "python",
            "cloud",
            "aws",
            "azure",
            "google cloud",
            "docker",
            "kubernetes",
            "iam",
            "identity"
        ]

        # Locations the user is willing to work in
        self.preferred_locations = [
            "helsinki",
            "espoo",
            "vantaa",
            "finland"
        ]
        self.priority_locations = [
          "helsinki",
           "espoo",
           "vantaa"
        ]

        self.secondary_locations = [
          "finland"
         ]

        self.remote_allowed = True
        self.hybrid_allowed = True
        self.onsite_allowed = True
        self.shift_allowed = True
        self.weekend_allowed = True
        self.training_allowed = True
        

        # User accepts remote work
        self.remote_allowed = True

        # User accepts hybrid work
        self.hybrid_allowed = True

        # User accepts onsite work
        self.onsite_allowed = True

        # User accepts shift/weekend work
        self.shift_allowed = True

        # User accepts training/internship opportunities
        self.training_allowed = True

        # User accepts paid and unpaid opportunities
        self.paid_allowed = True
        self.unpaid_allowed = True