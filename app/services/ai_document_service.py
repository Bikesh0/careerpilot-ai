from app.ai.profile_loader import ProfileLoader
from app.ai.resume_builder import ResumeBuilder
from app.ai.resume_generator import ResumeGenerator
from app.ai.cover_letter_builder import CoverLetterBuilder
from app.ai.cover_letter_generator import CoverLetterGenerator


class AIDocumentService:

    def __init__(self):

        self.profile_loader = ProfileLoader()

        self.resume_builder = ResumeBuilder()

        self.resume_generator = ResumeGenerator()

        self.cover_builder = CoverLetterBuilder()

        self.cover_generator = CoverLetterGenerator()

    def generate_resume(self, job):

        profile = self.profile_loader.load()

        tailored_resume = self.resume_builder.build(
            profile,
            job
        )

        return self.resume_generator.generate(
            tailored_resume,
            profile,
            job
        )

    def generate_cover_letter(self, job):

        profile = self.profile_loader.load()

        letter = self.cover_builder.build(
            profile,
            job
        )

        return self.cover_generator.generate(
            letter,
            profile,
            job
        )