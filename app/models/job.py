class Job:

    def __init__(
        self,
        title,
        company,
        location,
        url,
        description,
        source
    ):
        self.title = title
        self.company = company
        self.location = location
        self.url = url
        self.description = description
        self.source = source

    def to_dict(self):
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "description": self.description,
            "source": self.source
        }

    def __str__(self):
        return f"{self.title} - {self.company} ({self.location})"