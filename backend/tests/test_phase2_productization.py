import unittest
from unittest.mock import Mock, patch

from app.api.v1.activities import get_recent_activities
from app.api.v1.notifications import get_my_notifications
from app.api.v1.users import list_users
from app.models.notification import Notification
from app.models.task import TaskStatus
from app.models.user import UserRole
from app.services.ai_insight_service import AIInsightService
from app.services.notification_engine import NotificationEngine
from app.services.notification_scheduler import NotificationScheduler
from app.services.task_service import TaskService
from app.utils.task_ultis import business_today
from tests.helpers import close_session, create_activity, create_department, create_task, create_user, make_session


class PaginationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        self.department = create_department(self.db, "Engineering")
        self.admin = create_user(self.db, self.department, "admin@example.com", UserRole.ADMIN)
        self.staff = create_user(self.db, self.department, "staff@example.com", UserRole.STAFF)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_task_service_paginates_authorized_tasks(self) -> None:
        for index in range(3):
            create_task(self.db, self.admin, self.staff, title=f"Task {index}", status=TaskStatus.TODO)

        tasks, total = TaskService(self.db).list_tasks(self.staff, page=2, page_size=2)

        self.assertEqual(total, 3)
        self.assertEqual(len(tasks), 1)

    def test_user_endpoint_returns_page_metadata(self) -> None:
        create_user(self.db, self.department, "second@example.com", UserRole.STAFF)

        result = list_users(current_user=self.admin, search="", page=1, page_size=2, db=self.db)

        self.assertEqual(result.total, 3)
        self.assertEqual(result.pages, 2)
        self.assertEqual(len(result.items), 2)

    def test_notification_endpoint_returns_page_metadata(self) -> None:
        for index in range(3):
            self.db.add(Notification(user_id=self.staff.id, title=f"Thông báo {index}", message="Nội dung"))
        self.db.commit()

        result = get_my_notifications(page=2, page_size=2, db=self.db, current_user=self.staff)

        self.assertEqual(result.total, 3)
        self.assertEqual(result.pages, 2)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.unread_count, 3)

    def test_activity_endpoint_returns_page_metadata(self) -> None:
        for index in range(3):
            create_activity(self.db, self.staff, f"activity {index}")

        result = get_recent_activities(page=2, page_size=2, db=self.db, current_user=self.admin)

        self.assertEqual(result.total, 3)
        self.assertEqual(result.pages, 2)
        self.assertEqual(len(result.data), 1)


class SchedulerAndInsightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        department = create_department(self.db, "Engineering")
        self.admin = create_user(self.db, department, "admin@example.com", UserRole.ADMIN)
        self.staff = create_user(self.db, department, "staff@example.com", UserRole.STAFF)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_scheduler_run_once_uses_independent_session(self) -> None:
        db = Mock()
        with patch("app.services.notification_scheduler.SessionLocal", return_value=db), patch(
            "app.services.notification_scheduler.NotificationEngine"
        ) as engine_class:
            NotificationScheduler.run_once()

        engine_class.assert_called_once_with(db)
        engine_class.return_value.check_all.assert_called_once_with()
        db.close.assert_called_once_with()

    def test_insights_are_role_aware_and_utf8(self) -> None:
        staff_insights = AIInsightService.generate_insights({"role": "staff", "own_overdue_tasks": 1})
        manager_insights = AIInsightService.generate_insights({"role": "manager", "team_avg_kpi": 82, "team_size": 3})
        admin_insights = AIInsightService.generate_insights({"role": "admin", "system_avg_kpi": 75})

        self.assertIn("quá hạn", staff_insights[0].title)
        self.assertIn("nhóm", manager_insights[0].title)
        self.assertIn("hệ thống", admin_insights[0].title)

    def test_notification_engine_deduplicates_daily_notifications(self) -> None:
        create_task(
            self.db,
            self.admin,
            self.staff,
            title="Near deadline",
            status=TaskStatus.TODO,
            deadline=business_today(),
        )

        engine = NotificationEngine(self.db)
        engine.check_user(self.staff.id)
        engine.check_user(self.staff.id)

        notifications = self.db.query(Notification).filter(Notification.user_id == self.staff.id).all()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].metadata_json["notification_type"], "near_deadline")


if __name__ == "__main__":
    unittest.main()
