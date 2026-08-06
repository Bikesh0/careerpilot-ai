from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


class DocumentStyle:

    @staticmethod
    def title(paragraph):

        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        run = paragraph.runs[0]

        run.font.name = "Calibri"

        run.font.size = Pt(22)

        run.bold = True

    @staticmethod
    def heading(paragraph):

        run = paragraph.runs[0]

        run.font.name = "Calibri"

        run.font.size = Pt(14)

        run.bold = True

    @staticmethod
    def normal(paragraph):

        for run in paragraph.runs:

            run.font.name = "Calibri"

            run.font.size = Pt(11)