import unittest

from fastapi import HTTPException

from app.models.project import Project, ProjectMemberRole
from app.models.user import UserRole
from app.schemas.project import AddMemberRequest
from app.services.project_service import ProjectService
from tests.helpers import close_session, create_department, create_user, make_session


class ProjectMembershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.engineering = create_department(self.db, "Engineering")
        self.sales = create_department(self.db, "Sales")
        self.admin = create_user(self.db, self.engineering, "admin@example.com", UserRole.ADMIN)
        self.manager = create_user(self.db, self.engineering, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, self.engineering, "staff@example.com", UserRole.STAFF)
        self.other_staff = create_user(self.db, self.sales, "other@example.com", UserRole.STAFF)
        self.project = Project(
            name="KPI Project",
            code="PRJ-TEST",
            status="ACTIVE",
            department_id=self.engineering.id,
            manager_id=self.manager.id,
            created_by=self.admin.id,
        )
        self.db.add(self.project)
        self.db.commit()
        self.db.refresh(self.project)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_manager_cannot_add_user_outside_department(self) -> None:
        with self.assertRaises(HTTPException) as context:
            ProjectService(self.db).add_member(
                self.project.id,
                AddMemberRequest(user_id=self.other_staff.id, role=ProjectMemberRole.MEMBER),
                self.manager,
            )
        self.assertEqual(context.exception.status_code, 403)

    def test_active_contribution_share_cannot_exceed_100(self) -> None:
        service = ProjectService(self.db)
        service.add_member(
            self.project.id,
            AddMemberRequest(user_id=self.staff.id, role=ProjectMemberRole.MEMBER, contribution_share=80),
            self.admin,
        )
        with self.assertRaises(HTTPException) as context:
            service.add_member(
                self.project.id,
                AddMemberRequest(user_id=self.other_staff.id, role=ProjectMemberRole.MEMBER, contribution_share=30),
                self.admin,
            )
        self.assertEqual(context.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
