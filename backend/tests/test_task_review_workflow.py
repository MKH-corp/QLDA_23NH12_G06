import unittest

from fastapi import HTTPException

from app.models.task import TaskStatus
from app.models.user import UserRole
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService
from tests.helpers import close_session, create_department, create_user, make_session


class TaskReviewWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        department = create_department(self.db, "Engineering")
        self.manager = create_user(self.db, department, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, department, "staff@example.com", UserRole.STAFF)
        self.reviewer = create_user(self.db, department, "reviewer@example.com", UserRole.STAFF)
        self.service = TaskService(self.db)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_assignee_must_submit_task_before_manager_approval(self) -> None:
        task = self._create_task(reviewer_id=self.manager.id)

        with self.assertRaises(HTTPException) as context:
            self.service.update_task(self.staff, task.id, TaskUpdate(status=TaskStatus.DONE))
        self.assertEqual(context.exception.status_code, 409)

        submitted = self.service.update_task(
            self.staff,
            task.id,
            TaskUpdate(status=TaskStatus.IN_REVIEW),
        )
        approved = self.service.update_task(
            self.manager,
            submitted.id,
            TaskUpdate(status=TaskStatus.DONE),
        )

        self.assertEqual(approved.status, TaskStatus.DONE)
        self.assertIsNotNone(approved.done_at)

    def test_reviewer_can_read_and_return_submitted_task(self) -> None:
        task = self._create_task(reviewer_id=self.reviewer.id)
        self.service.update_task(self.staff, task.id, TaskUpdate(status=TaskStatus.IN_REVIEW))

        visible = self.service.get_task_for_actor(self.reviewer, task.id)
        returned = self.service.update_task(
            self.reviewer,
            visible.id,
            TaskUpdate(status=TaskStatus.DOING),
        )

        self.assertEqual(returned.status, TaskStatus.DOING)
        self.assertEqual(returned.reopen_count, 1)

    def test_new_task_cannot_start_as_done(self) -> None:
        with self.assertRaises(HTTPException) as context:
            self.service.create_task(
                self.manager,
                TaskCreate(
                    title="Invalid shortcut",
                    status=TaskStatus.DONE,
                    assignee_id=self.staff.id,
                    department_id=self.staff.department_id,
                ),
            )
        self.assertEqual(context.exception.status_code, 422)

    def _create_task(self, reviewer_id: int):
        return self.service.create_task(
            self.manager,
            TaskCreate(
                title="Review workflow",
                assignee_id=self.staff.id,
                reviewer_id=reviewer_id,
                department_id=self.staff.department_id,
            ),
        )


if __name__ == "__main__":
    unittest.main()
