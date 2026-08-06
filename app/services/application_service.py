from datetime import datetime

from app.database.application_tracker import ApplicationTracker
from app.database.models import Application


class ApplicationService:

    def __init__(self):

        self.tracker = ApplicationTracker()

    def save_job(self, job):

        application = Application(

            company=job.company,

            title=job.title,

            location=job.location,

            source=job.source,

            status="Saved",

            applied_date=datetime.now().strftime("%Y-%m-%d")

        )

        self.tracker.save(application)

    def get_all(self):

        return self.tracker.get_all()

    def update_status(self, app_id, status):

        self.tracker.update_status(app_id, status)

    def delete(self, app_id):

        self.tracker.delete(app_id)