from datetime import datetime

from app.database.project_tracker import ProjectTracker, PROJECT_STATUSES
from app.database.models import Project


_COLUMNS = (
    "id",
    "skill_key",
    "skill_display",
    "title",
    "description",
    "status",
    "created_date",
    "updated_date",
    "source_job_url",
    "notes",
    "cv_bullet",
)


def _row_to_dict(row):
    if row is None:
        return None

    return dict(zip(_COLUMNS, row))


class ProjectService:

    def __init__(self):
        self.tracker = ProjectTracker()

    def start_project(
        self,
        skill_key,
        skill_display,
        title,
        description,
        source_job_url="",
    ):
        """
        Create a new project record with status "Planned".

        This is the only way a project comes into existence - always
        an explicit user action (clicking "Start this project" on a
        skill-gap recommendation), never automatic.
        """

        project = Project(
            skill_key=skill_key,
            skill_display=skill_display,
            title=title,
            description=description,
            status="Planned",
            created_date=datetime.now().strftime("%Y-%m-%d"),
            source_job_url=source_job_url,
        )

        return self.tracker.create(project)

    def get_all(self):
        return [_row_to_dict(row) for row in self.tracker.get_all()]

    def get(self, project_id):
        return _row_to_dict(self.tracker.get(project_id))

    def update_status(self, project_id, status):
        if status not in PROJECT_STATUSES:
            raise ValueError(f"Unknown project status: {status!r}")

        self.tracker.update_status(
            project_id,
            status,
            datetime.now().strftime("%Y-%m-%d"),
        )

    def append_note(self, project_id, note_entry):
        self.tracker.append_notes(
            project_id,
            note_entry,
            datetime.now().strftime("%Y-%m-%d"),
        )

    def set_cv_bullet(self, project_id, cv_bullet):
        self.tracker.set_cv_bullet(
            project_id,
            cv_bullet,
            datetime.now().strftime("%Y-%m-%d"),
        )

    def verified_skill_keys(self):
        """
        The set of skill_key values with at least one Verified project
        - what app.ai.cv_strength uses to recognize real, completed
        practical evidence beyond the profile's own text.
        """

        return {
            row["skill_key"]
            for row in self.get_all()
            if row["status"] == "Verified"
        }

    def statistics(self):
        return {
            "total": len(self.tracker.get_all()),
            "planned": self.tracker.count_status("Planned"),
            "in_progress": self.tracker.count_status("In Progress"),
            "completed": self.tracker.count_status("Completed"),
            "verified": self.tracker.count_status("Verified"),
        }
