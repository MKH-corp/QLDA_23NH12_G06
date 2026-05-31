import unittest
from datetime import date, timedelta

from fastapi import HTTPException

from app.models.project import ProjectMemberRole, ProjectStatus
from app.models.task import Task, TaskStatus
from app.models.user import UserRole
from app.schemas.project import (
    AddMemberRequest,
    MilestoneCreate,
    MilestoneUpdate,
    ProjectCreate,
)
from app.services.project_service import ProjectService
from tests.helpers import (
    close_session,
    create_department,
    create_task,
    create_user,
    make_session,
)


class ProjectManagementModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.engineering = create_department(self.db, "Engineering")
        self.sales = create_department(self.db, "Sales")
        self.admin = create_user(self.db, self.engineering, "admin@example.com", UserRole.ADMIN)
        self.manager = create_user(self.db, self.engineering, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, self.engineering, "staff@example.com", UserRole.STAFF)
        self.service = ProjectService(self.db)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_manager_cannot_create_project_outside_department(self) -> None:
        with self.assertRaises(HTTPException) as context:
            self.service.create_project(
                ProjectCreate(name="Sales Project", department_id=self.sales.id),
                self.manager,
            )
        self.assertEqual(context.exception.status_code, 403)

    def test_project_rejects_invalid_date_range(self) -> None:
        with self.assertRaises(HTTPException) as context:
            self.service.create_project(
                ProjectCreate(
                    name="Invalid Dates",
                    department_id=self.engineering.id,
                    start_date=date(2026, 6, 2),
                    end_date=date(2026, 6, 1),
                ),
                self.admin,
            )
        self.assertEqual(context.exception.status_code, 422)

    def test_selected_manager_is_added_as_project_manager(self) -> None:
        project = self._create_project()
        member = self.service.repo.get_member(project.id, self.manager.id)
        self.assertIsNotNone(member)
        self.assertEqual(member.role, ProjectMemberRole.PROJECT_MANAGER)
        self.assertTrue(member.is_active)

    def test_delete_archives_project_with_tasks_and_retains_task_link(self) -> None:
        project = self._create_project()
        task = create_task(
            self.db,
            self.manager,
            self.staff,
            title="Retained task",
            status=TaskStatus.TODO,
            project_id=project.id,
        )

        self.service.delete_project(project.id, self.admin)

        stored = self.service._get_project_or_404(project.id)
        retained_task = self.db.get(Task, task.id)
        self.assertEqual(stored.status, ProjectStatus.ARCHIVED.value)
        self.assertIsNotNone(stored.archived_at)
        self.assertEqual(retained_task.project_id, project.id)

    def test_report_contains_real_member_and_task_statistics(self) -> None:
        project = self._create_project()
        self.service.add_member(
            project.id,
            AddMemberRequest(
                user_id=self.staff.id,
                role=ProjectMemberRole.MEMBER,
                contribution_share=60,
            ),
            self.admin,
        )
        create_task(
            self.db,
            self.manager,
            self.staff,
            title="Done task",
            status=TaskStatus.DONE,
            project_id=project.id,
        )
        create_task(
            self.db,
            self.manager,
            self.staff,
            title="Overdue task",
            status=TaskStatus.TODO,
            deadline=date.today() - timedelta(days=1),
            project_id=project.id,
        )

        report = self.service.get_report(project.id, self.admin)
        staff_report = next(item for item in report.member_performance if item.user_id == self.staff.id)

        self.assertEqual(report.analytics.total_tasks, 2)
        self.assertEqual(report.task_status_breakdown["done"], 1)
        self.assertEqual(report.analytics.overdue_tasks, 1)
        self.assertEqual(staff_report.total_tasks, 2)
        self.assertEqual(staff_report.done_tasks, 1)
        self.assertEqual(staff_report.overdue_tasks, 1)
        self.assertEqual(staff_report.task_completion_percentage, 50)

    def test_milestone_can_be_updated_and_deleted(self) -> None:
        project = self._create_project()
        milestone = self.service.create_milestone(
            project.id,
            MilestoneCreate(title="Phase 1", weight=2),
            self.admin,
        )

        updated = self.service.update_milestone(
            project.id,
            milestone.id,
            MilestoneUpdate(title="Phase 1 reviewed", weight=3),
            self.admin,
        )
        self.assertEqual(updated.title, "Phase 1 reviewed")
        self.assertEqual(updated.weight, 3)

        self.service.delete_milestone(project.id, milestone.id, self.admin)
        self.assertIsNone(self.service.repo.get_milestone(milestone.id))

    def _create_project(self):
        return self.service.create_project(
            ProjectCreate(
                name="Platform",
                code="PRJ-PLATFORM",
                department_id=self.engineering.id,
                manager_id=self.manager.id,
                status=ProjectStatus.ACTIVE,
            ),
            self.admin,
        )


if __name__ == "__main__":
    unittest.main()
