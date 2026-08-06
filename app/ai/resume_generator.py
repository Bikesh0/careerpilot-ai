from pathlib import Path
from datetime import datetime

from app.documents.resume_template import ResumeTemplate
from app.documents.document_style import DocumentStyle


class ResumeGenerator:

    def __init__(self):

        self.output_folder = Path("output")
        self.output_folder.mkdir(exist_ok=True)

    def generate(self, tailored_resume, profile, job):

        document = ResumeTemplate.create()

        # ============================
        # Header
        # ============================

        title = document.add_heading(
            profile.get("name", ""),
            level=0
        )

        DocumentStyle.title(title)

        p = document.add_paragraph(
            f'{profile.get("email", "")} | {profile.get("phone", "")}'
        )
        DocumentStyle.normal(p)

        p = document.add_paragraph(
            profile.get("location", "")
        )
        DocumentStyle.normal(p)

        p = document.add_paragraph(
            profile.get("linkedin", "")
        )
        DocumentStyle.normal(p)

        # ============================
        # Professional Summary
        # ============================

        heading = document.add_heading(
            "Professional Summary",
            level=1
        )
        DocumentStyle.heading(heading)

        p = document.add_paragraph(
            tailored_resume.get("summary", "")
        )
        DocumentStyle.normal(p)

        # ============================
        # Skills
        # ============================

        heading = document.add_heading(
            "Skills",
            level=1
        )
        DocumentStyle.heading(heading)

        for skill in tailored_resume.get("skills", []):

            p = document.add_paragraph(
                skill,
                style="List Bullet"
            )
            DocumentStyle.normal(p)

        # ============================
        # Experience
        # ============================

        heading = document.add_heading(
            "Experience",
            level=1
        )
        DocumentStyle.heading(heading)

        for exp in tailored_resume.get("experience", []):

            sub = document.add_heading(
                f'{exp.get("title", "")} - {exp.get("company", "")}',
                level=2
            )

            DocumentStyle.heading(sub)

            bullets = (
                exp.get("bullets")
                or exp.get("description")
                or []
            )

            for bullet in bullets:

                p = document.add_paragraph(
                    bullet,
                    style="List Bullet"
                )

                DocumentStyle.normal(p)

        # ============================
        # Education
        # ============================

        heading = document.add_heading(
            "Education",
            level=1
        )
        DocumentStyle.heading(heading)

        for edu in profile.get("education", []):

            p = document.add_paragraph(
                f'{edu.get("degree", "")}\n'
                f'{edu.get("school", "")}'
            )

            DocumentStyle.normal(p)

        # ============================
        # Certifications
        # ============================

        heading = document.add_heading(
            "Certifications",
            level=1
        )
        DocumentStyle.heading(heading)

        for cert in profile.get("certifications", []):

            p = document.add_paragraph(
                cert,
                style="List Bullet"
            )

            DocumentStyle.normal(p)

        # ============================
        # Target Position
        # ============================

        heading = document.add_heading(
            "Target Position",
            level=1
        )
        DocumentStyle.heading(heading)

        p = document.add_paragraph(job.title)
        DocumentStyle.normal(p)

        p = document.add_paragraph(job.company)
        DocumentStyle.normal(p)

        # ============================
        # Generated
        # ============================

        heading = document.add_heading(
            "Generated",
            level=1
        )
        DocumentStyle.heading(heading)

        p = document.add_paragraph(
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        DocumentStyle.normal(p)

        filename = self.output_folder / (
            f"{job.title.replace(' ', '_')}_Resume.docx"
        )

        document.save(filename)

        return filename