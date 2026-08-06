from app.parsers.cv_parser import CVParser
from app.ai.profile_extractor import ProfileExtractor
from app.ai.resume_builder import ResumeBuilder
from app.ai.resume_generator import ResumeGenerator


class DocumentService:

    def __init__(self):

        self.parser = CVParser()

        self.extractor = ProfileExtractor()

        self.builder = ResumeBuilder()

        self.generator = ResumeGenerator()

    def generate_resume(self, cv_path, job):

        # Parse CV
        cv_text = self.parser.parse(cv_path)

        # AI extracts profile
        profile = self.extractor.extract(cv_text)

        # AI builds tailored resume
        tailored_resume = self.builder.build(
            profile,
            job
        )

        # Generate DOCX
        return self.generator.generate(
            tailored_resume,
            profile,
            job
        )