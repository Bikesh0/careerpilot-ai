from app.parsers.cv_parser import CVParser


class ProfileService:

    def __init__(self):

        self.parser = CVParser()

    def load(self, cv_path):

        cv_text = self.parser.parse(cv_path)

        return {

            "raw_cv": cv_text

        }