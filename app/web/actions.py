from pathlib import Path
from flask import send_file

from app.database.application_tracker import ApplicationTracker


class WebActions:

    def __init__(self):

        self.tracker = ApplicationTracker()

    def save_application(self, job):

        self.tracker.add_application(

            title=job.title,

            company=job.company,

            location=job.location,

            source=job.source

        )

    def latest_resume(self):

        folder = Path("resumes")

        files = list(folder.glob("*"))

        if not files:

            return None

        files.sort(key=lambda f: f.stat().st_mtime)

        return files[-1]

    def latest_cover_letter(self):

        folder = Path("cover_letters")

        files = list(folder.glob("*"))

        if not files:

            return None

        files.sort(key=lambda f: f.stat().st_mtime)

        return files[-1]