import unittest

from fastapi import HTTPException

from app.models.project import Project, ProjectMemberRole
from app.models.task import TaskStatus
from app.models.user import UserRole
from app.schemas.project import AddMemberRequest, ProjectUpdate, UpdateMemberRoleRequest
from app.services.project_service import ProjectService
from tests.helpers import close_session, create_department, create_task, create_user, make_session


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

    def test_member_with_active_project_task_cannot_be_removed_or_deactivated(self) -> None:
        service = ProjectService(self.db)
        service.add_member(
            self.project.id,
            AddMemberRequest(user_id=self.staff.id),
            self.admin,
        )
        create_task(
            self.db,
            self.manager,
            self.staff,
            title="Still active",
            status=TaskStatus.TODO,
            project_id=self.project.id,
        )

        with self.assertRaises(HTTPException) as remove_context:
            service.remove_member(self.project.id, self.staff.id, self.admin)
        with self.assertRaises(HTTPException) as deactivate_context:
            service.update_member_role(
                self.project.id,
                self.staff.id,
                UpdateMemberRoleRequest(is_active=False),
                self.admin,
            )

        self.assertEqual(remove_context.exception.status_code, 409)
        self.assertEqual(deactivate_context.exception.status_code, 409)

    def test_changing_manager_demotes_previous_project_manager(self) -> None:
        replacement = create_user(
            self.db,
            self.engineering,
            "replacement@example.com",
            UserRole.MANAGER,
        )
        service = ProjectService(self.db)
        service._ensure_project_manager_membership(self.project.id, self.manager.id, self.admin.id)

        service.update_project(
            self.project.id,
            ProjectUpdate(manager_id=replacement.id),
            self.admin,
        )

        previous_member = service.repo.get_member(self.project.id, self.manager.id)
        replacement_member = service.repo.get_member(self.project.id, replacement.id)
        self.assertEqual(previous_member.role, ProjectMemberRole.MEMBER)
        self.assertEqual(replacement_member.role, ProjectMemberRole.PROJECT_MANAGER)
        self.assertTrue(replacement_member.is_active)


if __name__ == "__main__":
    unittest.main()
