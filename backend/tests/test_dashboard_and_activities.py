import unittest

from fastapi import HTTPException

from app.api.deps import require_manager_or_admin
from app.api.v1.activities import get_recent_activities
from app.models.user import UserRole
from app.services.dashboard_service import DashboardService
from tests.helpers import (
    close_session,
    create_activity,
    create_department,
    create_snapshot,
    create_user,
    make_session,
)


class DashboardAndActivityScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        engineering = create_department(self.db, "Engineering")
        business = create_department(self.db, "Business")
        self.admin = create_user(self.db, engineering, "admin@example.com", UserRole.ADMIN)
        self.manager = create_user(self.db, engineering, "manager@example.com", UserRole.MANAGER)
        self.engineer = create_user(self.db, engineering, "engineer@example.com", UserRole.STAFF)
        self.business_staff = create_user(self.db, business, "business@example.com", UserRole.STAFF)
        create_snapshot(self.db, self.engineer, 90, 3)
        create_snapshot(self.db, self.business_staff, 50, 1)
        create_activity(self.db, self.engineer, "engineering activity")
        create_activity(self.db, self.business_staff, "business activity")

    def tearDown(self) -> None:
        close_session(self.db)

    def test_staff_cannot_access_enterprise_dashboard(self) -> None:
        with self.assertRaises(HTTPException) as context:
            require_manager_or_admin(self.engineer)
        self.assertEqual(context.exception.status_code, 403)

    def test_manager_dashboard_is_scoped_to_department(self) -> None:
        dashboard = DashboardService(self.db).get_dashboard_data(self.manager)
        self.assertEqual(dashboard.stats.active_departments, 1)
        self.assertEqual(dashboard.stats.total_employees, 3)
        self.assertEqual([item.department_name for item in dashboard.top_performers], ["Engineering"])
        self.assertEqual([item.description for item in dashboard.recent_activities], ["engineering activity"])

    def test_activity_endpoint_scopes_staff_and_manager(self) -> None:
        staff_result = get_recent_activities(limit=20, db=self.db, current_user=self.engineer)
        manager_result = get_recent_activities(limit=20, db=self.db, current_user=self.manager)
        admin_result = get_recent_activities(limit=20, db=self.db, current_user=self.admin)
        self.assertEqual([item.description for item in staff_result.data], ["engineering activity"])
        self.assertEqual([item.description for item in manager_result.data], ["engineering activity"])
        self.assertEqual({item.description for item in admin_result.data}, {"engineering activity", "business activity"})


if __name__ == "__main__":
    unittest.main()
