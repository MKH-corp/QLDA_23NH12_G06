import unittest

from fastapi import HTTPException

from app.models.project import ProjectStatus, ProjectStatusHistory
from app.models.user import UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService
from tests.helpers import close_session, create_department, create_user, make_session


class ProjectLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.department = create_department(self.db, "Engineering")
        self.admin = create_user(self.db, self.department, "admin@example.com", UserRole.ADMIN)
        self.service = ProjectService(self.db)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_project_can_follow_valid_lifecycle_to_archive(self) -> None:
        project = self._create_project()
        for status in (
            ProjectStatus.ACTIVE,
            ProjectStatus.REVIEW,
            ProjectStatus.COMPLETED,
            ProjectStatus.ARCHIVED,
        ):
            project = self.service.update_project(project.id, ProjectUpdate(status=status), self.admin)

        stored = self.service._get_project_or_404(project.id)
        self.assertEqual(stored.status, ProjectStatus.ARCHIVED.value)
        self.assertIsNotNone(stored.archived_at)

    def test_project_rejects_invalid_transition(self) -> None:
        project = self._create_project()
        with self.assertRaises(HTTPException) as context:
            self.service.update_project(
                project.id,
                ProjectUpdate(status=ProjectStatus.ARCHIVED),
                self.admin,
            )
        self.assertEqual(context.exception.status_code, 422)

    def test_same_status_does_not_add_history_entry(self) -> None:
        project = self._create_project()
        self.service.update_project(project.id, ProjectUpdate(status=ProjectStatus.ACTIVE), self.admin)
        before = self.db.query(ProjectStatusHistory).filter(ProjectStatusHistory.project_id == project.id).count()
        self.service.update_project(project.id, ProjectUpdate(status=ProjectStatus.ACTIVE), self.admin)
        after = self.db.query(ProjectStatusHistory).filter(ProjectStatusHistory.project_id == project.id).count()
        self.assertEqual(before, after)

    def _create_project(self):
        return self.service.create_project(
            ProjectCreate(name="Platform", department_id=self.department.id),
            self.admin,
        )


if __name__ == "__main__":
    unittest.main()
