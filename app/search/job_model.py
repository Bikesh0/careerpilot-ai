class Job:


    def __init__(
        self,
        title,
        company,
        location,
        description,
        source="",
        url=""
    ):

        self.title = title

        self.company = company

        self.location = location

        self.description = description

        self.source = source

        self.url = url



    def to_dict(self):

        return {

            "title": self.title,

            "company": self.company,

            "location": self.location,

            "description": self.description,

            "source": self.source,

            "url": self.url

        }