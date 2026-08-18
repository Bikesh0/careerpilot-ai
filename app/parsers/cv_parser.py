from pathlib import Path
import pymupdf as fitz
from docx import Document


class CVParser:

    def parse(self, file_path):

        file_path = Path(file_path)

        if file_path.suffix.lower() == ".pdf":
            return self._parse_pdf(file_path)

        if file_path.suffix.lower() == ".docx":
            return self._parse_docx(file_path)

        raise ValueError("Unsupported CV format")

    def _parse_pdf(self, file_path):

        doc = fitz.open(file_path)

        text = ""

        for page in doc:

            text += page.get_text()

        return text

    def _parse_docx(self, file_path):

        doc = Document(file_path)

        text = []

        for paragraph in doc.paragraphs:

            if paragraph.text.strip():
                text.append(paragraph.text)

        return "\n".join(text)
    