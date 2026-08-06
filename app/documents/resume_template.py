from docx import Document
from docx.shared import Inches


class ResumeTemplate:

    @staticmethod
    def create():

        document = Document()

        section = document.sections[0]

        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

        return document