import unittest
from datetime import date, datetime, timedelta, timezone

from app.models.kpi_snapshot import KpiSnapshot
from app.models.task import TaskStatus
from app.models.user import UserRole
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.kpi_engine import KpiEngine
from app.services.task_service import TaskService
from app.utils.task_ultis import (
    business_day_utc_range,
    business_month_utc_range,
    business_period_key,
    business_today,
    completion_business_date,
)
from tests.helpers import close_session, create_department, create_task, create_user, make_session


class KpiEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        department = create_department(self.db, "Engineering")
        self.manager = create_user(self.db, department, "manager@example.com", UserRole.MANAGER)
        self.staff = create_user(self.db, department, "staff@example.com", UserRole.STAFF)
        self.now = datetime.now(timezone.utc).replace(tzinfo=None)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_on_time_task_gets_bonus(self) -> None:
        create_task(
            self.db,
            self.manager,
            self.staff,
            title="On time",
            status=TaskStatus.DONE,
            deadline=business_today(),
            done_at=self.now,
            base_weight=10,
        )
        snapshot = KpiEngine(self.db).recalculate_monthly_kpi(self.staff.id)
        self.assertEqual(snapshot.total_score, 12.0)
        self.assertEqual(snapshot.breakdown["on_time_bonus"], 2.0)

    def test_late_task_gets_penalty(self) -> None:
        create_task(
            self.db,
            self.manager,
            self.staff,
            title="Late",
            status=TaskStatus.DONE,
            deadline=business_today() - timedelta(days=2),
            done_at=self.now,
            base_weight=10,
        )
        snapshot = KpiEngine(self.db).recalculate_monthly_kpi(self.staff.id)
        self.assertEqual(snapshot.total_score, 9.0)
        self.assertEqual(snapshot.tasks_overdue, 1)

    def test_reopen_count_reduces_score(self) -> None:
        create_task(
            self.db,
            self.manager,
            self.staff,
            title="Reopened",
            status=TaskStatus.DONE,
            deadline=business_today(),
            done_at=self.now,
            base_weight=10,
            reopen_count=3,
        )
        snapshot = KpiEngine(self.db).recalculate_monthly_kpi(self.staff.id)
        self.assertEqual(snapshot.total_score, 10.8)
        self.assertEqual(snapshot.breakdown["reopen_penalty_amount"], -1.2)

    def test_task_service_refreshes_snapshot_for_create_reopen_and_delete(self) -> None:
        service = TaskService(self.db)
        created = service.create_task(
            self.manager,
            TaskCreate(
                title="Lifecycle",
                status=TaskStatus.DONE,
                deadline=business_today(),
                base_weight=10,
                assignee_id=self.staff.id,
                department_id=self.staff.department_id,
            ),
        )
        self.assertEqual(self._snapshot().total_score, 12.0)

        service.update_task(self.manager, created.id, TaskUpdate(status=TaskStatus.BLOCKED))
        self.assertEqual(self._snapshot().total_score, 0.0)

        service.update_task(self.manager, created.id, TaskUpdate(status=TaskStatus.DONE))
        self.assertEqual(self._snapshot().total_score, 12.0)

        service.delete_task(self.manager, created.id)
        self.assertEqual(self._snapshot().total_score, 0.0)

    def test_task_service_refreshes_both_snapshots_when_assignee_changes(self) -> None:
        second_staff = create_user(
            self.db,
            self.staff.department,
            "second@example.com",
            UserRole.STAFF,
        )
        service = TaskService(self.db)
        created = service.create_task(
            self.manager,
            TaskCreate(
                title="Transfer",
                status=TaskStatus.DONE,
                deadline=business_today(),
                base_weight=10,
                assignee_id=self.staff.id,
                department_id=self.staff.department_id,
            ),
        )

        service.update_task(self.manager, created.id, TaskUpdate(assignee_id=second_staff.id))

        self.assertEqual(self._snapshot(self.staff.id).total_score, 0.0)
        self.assertEqual(self._snapshot(second_staff.id).total_score, 12.0)

    def test_business_timezone_controls_month_and_deadline_boundaries(self) -> None:
        completed_at = datetime(2026, 5, 31, 18, 0)
        self.assertEqual(completion_business_date(completed_at), date(2026, 6, 1))
        self.assertEqual(business_period_key(completed_at.replace(tzinfo=timezone.utc)), "2026-06")
        self.assertEqual(
            business_month_utc_range(completed_at.replace(tzinfo=timezone.utc)),
            (datetime(2026, 5, 31, 17, 0), datetime(2026, 6, 30, 17, 0)),
        )
        self.assertEqual(
            business_day_utc_range(date(2026, 6, 1)),
            (
                datetime(2026, 5, 31, 17, 0, tzinfo=timezone.utc),
                datetime(2026, 6, 1, 17, 0, tzinfo=timezone.utc),
            ),
        )

    def _snapshot(self, user_id: int | None = None) -> KpiSnapshot:
        return self.db.query(KpiSnapshot).filter(KpiSnapshot.user_id == (user_id or self.staff.id)).one()


if __name__ == "__main__":
    unittest.main()
