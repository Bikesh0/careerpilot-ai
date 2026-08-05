class JobIntelligence:


    def detect_category(self, job):

        title = job.get("title", "")
        description = job.get("description", "")

        text = (
            title + " " + description
        ).lower()



        if any(word in text for word in [
            "soc",
            "siem",
            "incident",
            "threat",
            "security monitoring",
            "cybersecurity"
        ]):

            return "Security Operations"



        if any(word in text for word in [
            "cloud",
            "aws",
            "azure",
            "kubernetes",
            "docker",
            "devops"
        ]):

            return "Cloud Security"



        if any(word in text for word in [
            "network",
            "firewall",
            "routing",
            "switching"
        ]):

            return "Network Security"



        return "IT / Technology"



    def detect_level(self, job):

        text = (
            job.get("title", "")
            + " "
            + job.get("description", "")
        ).lower()



        if any(word in text for word in [
            "junior",
            "trainee",
            "intern",
            "graduate",
            "entry"
        ]):

            return "Junior"



        if any(word in text for word in [
            "senior",
            "lead",
            "architect",
            "manager"
        ]):

            return "Senior"



        return "Mid"



    def analyze(self, job):

        return {

            "category": self.detect_category(job),

            "level": self.detect_level(job)

        }