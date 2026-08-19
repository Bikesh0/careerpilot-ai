import pytest

from app.database.models import Project
from app.database.project_tracker import ProjectTracker, PROJECT_STATUSES
from app.services.project_service import ProjectService


def _tracker(tmp_path):
    return ProjectTracker(database_path=tmp_path / "careerpilot.db")


def test_create_and_get_project(tmp_path):
    tracker = _tracker(tmp_path)

    project = Project(
        skill_key="kubernetes",
        skill_display="Kubernetes",
        title="Local cluster deployment",
        description="Deploy a small multi-service app to a local cluster.",
        status="Planned",
        created_date="2026-08-20",
    )

    project_id = tracker.create(project)
    row = tracker.get(project_id)

    assert row is not None
    assert row[1] == "kubernetes"
    assert row[5] == "Planned"


def test_status_only_changes_via_explicit_update_call(tmp_path):
    """
    Regression test for the mission's explicit rule: a project's status
    must never change automatically. create() always stores exactly the
    status passed in (Planned, per ProjectService.start_project()), and
    update_status() is the only method that can change it afterward -
    there is no code path that flips status as a side effect of reading
    or displaying a project.
    """

    tracker = _tracker(tmp_path)

    project = Project(
        skill_key="docker",
        skill_display="Docker",
        title="Containerize an existing app",
        description="Write a Dockerfile for a small project.",
        status="Planned",
        created_date="2026-08-20",
    )
    project_id = tracker.create(project)

    for _ in range(3):
        assert tracker.get(project_id)[5] == "Planned"

    tracker.update_status(project_id, "In Progress", "2026-08-21")
    assert tracker.get(project_id)[5] == "In Progress"

    for _ in range(3):
        assert tracker.get(project_id)[5] == "In Progress"


def test_append_notes_accumulates_rather_than_overwrites(tmp_path):
    tracker = _tracker(tmp_path)

    project = Project(
        skill_key="git",
        skill_display="Git",
        title="Public portfolio repo",
        description="Move a project onto GitHub.",
        status="Planned",
        created_date="2026-08-20",
    )
    project_id = tracker.create(project)

    tracker.append_notes(project_id, "First note", "2026-08-20")
    tracker.append_notes(project_id, "Second note", "2026-08-21")

    notes = tracker.get(project_id)[9]

    assert "First note" in notes
    assert "Second note" in notes


def test_get_verified_by_skill_key_only_returns_verified_projects(tmp_path):
    tracker = _tracker(tmp_path)

    planned = Project(
        skill_key="terraform", skill_display="Terraform", title="A",
        description="d", status="Planned", created_date="2026-08-20",
    )
    verified = Project(
        skill_key="terraform", skill_display="Terraform", title="B",
        description="d", status="Verified", created_date="2026-08-20",
    )
    tracker.create(planned)
    verified_id = tracker.create(verified)

    results = tracker.get_verified_by_skill_key("terraform")

    assert len(results) == 1
    assert results[0][0] == verified_id


def test_project_service_start_project_and_verified_skill_keys(tmp_path):
    service = ProjectService()
    service.tracker = _tracker(tmp_path)

    project_id = service.start_project(
        skill_key="siem",
        skill_display="SIEM",
        title="SIEM dashboard from lab logs",
        description="Build a dashboard.",
    )

    assert service.verified_skill_keys() == set()

    service.update_status(project_id, "Verified")

    assert service.verified_skill_keys() == {"siem"}


def test_project_service_rejects_an_unknown_status(tmp_path):
    service = ProjectService()
    service.tracker = _tracker(tmp_path)

    project_id = service.start_project(
        skill_key="python", skill_display="Python", title="A", description="d",
    )

    with pytest.raises(ValueError):
        service.update_status(project_id, "Done")


def test_all_project_statuses_are_the_ones_the_mission_specifies():
    assert set(PROJECT_STATUSES) == {
        "Planned", "In Progress", "Completed", "Verified",
    }
