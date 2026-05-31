import unittest

from fastapi import HTTPException

from app.api.deps import require_admin, require_authenticated_user, require_manager_or_admin
from app.models.task import TaskStatus
from app.models.user import UserRole
from app.schemas.task import TaskCreate
from app.schemas.user import UserUpdate
from app.services.auth_service import AuthService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from tests.helpers import close_session, create_department, create_task, create_user, make_session


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.department = create_department(self.db, "Engineering")
        self.admin = create_user(self.db, self.department, "admin@example.com", UserRole.ADMIN)
        self.manager = create_user(self.db, self.department, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, self.department, "staff@example.com", UserRole.STAFF)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_authenticate_user_accepts_valid_password(self) -> None:
        user = AuthService(self.db).authenticate_user("staff@example.com", "Password@123")
        self.assertEqual(user.id, self.staff.id)

    def test_authenticate_user_rejects_invalid_password(self) -> None:
        with self.assertRaises(HTTPException) as context:
            AuthService(self.db).authenticate_user("staff@example.com", "wrong-password")
        self.assertEqual(context.exception.status_code, 401)

    def test_authenticate_user_rejects_inactive_account(self) -> None:
        self.staff.is_active = False
        self.db.commit()
        with self.assertRaises(HTTPException) as context:
            AuthService(self.db).authenticate_user("staff@example.com", "Password@123")
        self.assertEqual(context.exception.status_code, 403)

    def test_role_dependencies_enforce_access(self) -> None:
        self.assertEqual(require_authenticated_user(self.staff).id, self.staff.id)
        self.assertEqual(require_manager_or_admin(self.manager).id, self.manager.id)
        self.assertEqual(require_admin(self.admin).id, self.admin.id)
        with self.assertRaises(HTTPException):
            require_admin(self.staff)
        with self.assertRaises(HTTPException):
            require_manager_or_admin(self.staff)

    def test_empty_password_update_keeps_existing_password_hash(self) -> None:
        old_hash = self.staff.password_hash
        updated = UserService(self.db).update_user(self.staff.id, UserUpdate(password=""))
        self.assertEqual(updated.password_hash, old_hash)

    def test_delete_user_soft_deactivates_account(self) -> None:
        UserService(self.db).delete_user(self.staff.id)
        self.assertFalse(self.staff.is_active)
        self.assertIsNotNone(self.db.get(type(self.staff), self.staff.id))


class TaskAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.engineering = create_department(self.db, "Engineering")
        self.business = create_department(self.db, "Business")
        self.manager = create_user(self.db, self.engineering, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, self.engineering, "staff@example.com", UserRole.STAFF)
        self.other_staff = create_user(self.db, self.business, "other@example.com", UserRole.STAFF)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_staff_cannot_create_task(self) -> None:
        payload = TaskCreate(
            title="Forbidden",
            assignee_id=self.staff.id,
            department_id=self.engineering.id,
        )
        with self.assertRaises(HTTPException) as context:
            TaskService(self.db).create_task(self.staff, payload)
        self.assertEqual(context.exception.status_code, 403)

    def test_manager_cannot_access_other_department_task(self) -> None:
        task = create_task(
            self.db,
            self.manager,
            self.other_staff,
            title="Other department",
            status=TaskStatus.TODO,
        )
        with self.assertRaises(HTTPException) as context:
            TaskService(self.db).get_task_for_actor(self.manager, task.id)
        self.assertEqual(context.exception.status_code, 403)

    def test_staff_list_only_returns_assigned_tasks(self) -> None:
        own_task = create_task(
            self.db,
            self.manager,
            self.staff,
            title="Own task",
            status=TaskStatus.TODO,
        )
        create_task(
            self.db,
            self.manager,
            self.other_staff,
            title="Other task",
            status=TaskStatus.TODO,
        )
        tasks, total = TaskService(self.db).list_tasks(self.staff)
        self.assertEqual([item.id for item in tasks], [own_task.id])
        self.assertEqual(total, 1)

    def test_staff_cannot_delete_assigned_task(self) -> None:
        task = create_task(
            self.db,
            self.manager,
            self.staff,
            title="Assigned task",
            status=TaskStatus.TODO,
        )
        with self.assertRaises(HTTPException) as context:
            TaskService(self.db).delete_task(self.staff, task.id)
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
