self.cover_builder = CoverLetterBuilder()

self.cover_generator = CoverLetterGenerator()

def generate_cover_letter(self, cv_path, job):

    cv_text = self.parser.parse(cv_path)

    profile = self.extractor.extract(cv_text)

    letter = self.cover_builder.build(

        profile,

        job

    )

    return self.cover_generator.generate(

        letter,

        profile,

        job

    )