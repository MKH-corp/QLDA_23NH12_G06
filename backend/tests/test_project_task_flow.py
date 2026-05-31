import unittest

from fastapi import HTTPException

from app.models.project import Project, ProjectMemberRole
from app.models.task import TaskStatus
from app.models.user import UserRole
from app.schemas.project import AddMemberRequest
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from tests.helpers import close_session, create_department, create_user, make_session


class ProjectTaskFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.department = create_department(self.db, "Engineering")
        self.admin = create_user(self.db, self.department, "admin@example.com", UserRole.ADMIN)
        self.manager = create_user(self.db, self.department, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, self.department, "staff@example.com", UserRole.STAFF)
        self.other_staff = create_user(self.db, self.department, "other@example.com", UserRole.STAFF)
        self.project_a = self._create_project("PRJ-A")
        self.project_b = self._create_project("PRJ-B")
        membership_service = ProjectService(self.db)
        for project in (self.project_a, self.project_b):
            membership_service.add_member(
                project.id,
                AddMemberRequest(user_id=self.staff.id, role=ProjectMemberRole.MEMBER),
                self.admin,
            )

    def tearDown(self) -> None:
        close_session(self.db)

    def _create_project(self, code: str) -> Project:
        project = Project(
            name=code,
            code=code,
            status="ACTIVE",
            department_id=self.department.id,
            manager_id=self.manager.id,
            created_by=self.admin.id,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def _create_project_task(self, project_id: int, status: TaskStatus = TaskStatus.TODO):
        return TaskService(self.db).create_task(
            self.manager,
            TaskCreate(
                title="Project task",
                status=status,
                assignee_id=self.staff.id,
                department_id=self.department.id,
                project_id=project_id,
            ),
        )

    def test_task_can_be_assigned_to_project_member(self) -> None:
        task = self._create_project_task(self.project_a.id)
        self.assertEqual(task.project_id, self.project_a.id)
        self.assertEqual(ProjectService(self.db).repo.get_task_counts(self.project_a.id)["total"], 1)

    def test_task_cannot_assign_to_non_project_member(self) -> None:
        with self.assertRaises(HTTPException) as context:
            TaskService(self.db).create_task(
                self.manager,
                TaskCreate(
                    title="Invalid assignee",
                    assignee_id=self.other_staff.id,
                    department_id=self.department.id,
                    project_id=self.project_a.id,
                ),
            )
        self.assertEqual(context.exception.status_code, 422)

    def test_project_progress_recalculates_when_task_done(self) -> None:
        task = self._create_project_task(self.project_a.id)
        self.assertEqual(self.project_a.progress_percentage, 0)
        TaskService(self.db).update_task(self.manager, task.id, TaskUpdate(status=TaskStatus.DONE))
        self.db.refresh(self.project_a)
        self.assertEqual(self.project_a.progress_percentage, 70)

    def test_changing_task_project_recalculates_both_projects(self) -> None:
        task = self._create_project_task(self.project_a.id, TaskStatus.DONE)
        self.assertEqual(self.project_a.progress_percentage, 70)
        TaskService(self.db).update_task(self.manager, task.id, TaskUpdate(project_id=self.project_b.id))
        self.db.refresh(self.project_a)
        self.db.refresh(self.project_b)
        self.assertEqual(self.project_a.progress_percentage, 0)
        self.assertEqual(self.project_b.progress_percentage, 70)

    def test_get_tasks_filter_project_id(self) -> None:
        task_a = self._create_project_task(self.project_a.id)
        self._create_project_task(self.project_b.id)
        tasks, total = TaskService(self.db).list_tasks(self.manager, project_id=self.project_a.id)
        self.assertEqual(total, 1)
        self.assertEqual([task.id for task in tasks], [task_a.id])


if __name__ == "__main__":
    unittest.main()
