class JobRecord:


    def __init__(
        self,
        title,
        company,
        location,
        description,
        source,
        match_score,
        decision
    ):

        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.source = source
        self.match_score = match_score
        self.decision = decision