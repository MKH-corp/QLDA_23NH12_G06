from sqlalchemy.orm import Session
from datetime import timedelta
from app.models.notification import Notification
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.kpi_snapshot import KpiSnapshot
from app.utils.task_ultis import business_day_utc_range, business_period_key, business_today


class NotificationEngine:
    """Rule-based notification engine for automatic alerts"""

    def __init__(self, db: Session):
        self.db = db
        self.today = business_today()
        self.period_key = business_period_key()

    def check_all(self):
        """Run all notification checks for all users"""
        active_users = self.db.query(User).filter(User.is_active == True).all()
        for user in active_users:
            self.check_user(user.id)

    def check_user(self, user_id: int):
        """Run notification checks for a specific user"""
        self._check_overdue_tasks(user_id)
        self._check_near_deadline_tasks(user_id)
        self._check_blocked_tasks(user_id)
        self._check_low_kpi(user_id)
        self._check_excellent_performance(user_id)

    def _check_overdue_tasks(self, user_id: int):
        """Alert: User has overdue tasks"""
        overdue_tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status != TaskStatus.DONE,
            Task.deadline < self.today
        ).all()

        if overdue_tasks:
            if not self._notification_exists_today(user_id, "overdue_task"):
                task_ids = [t.id for t in overdue_tasks]
                notification = Notification(
                    user_id=user_id,
                    title=f"Bạn có {len(overdue_tasks)} công việc đã quá hạn",
                    message=f"Phát hiện {len(overdue_tasks)} công việc chưa hoàn thành đã vượt quá thời hạn. Vui lòng ưu tiên xử lý.",
                    type="danger",
                    severity="danger",
                    source="notification_engine",
                    metadata_json={
                        "notification_type": "overdue_task",
                        "overdue_task_ids": task_ids,
                        "overdue_count": len(overdue_tasks)
                    },
                    is_ai_generated=False
                )
                self.db.add(notification)
                self.db.commit()

    def _check_near_deadline_tasks(self, user_id: int):
        """Alert: User has tasks with deadline in next 2 days"""
        deadline_start = self.today
        deadline_end = self.today + timedelta(days=2)

        near_deadline_tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status != TaskStatus.DONE,
            Task.deadline >= deadline_start,
            Task.deadline <= deadline_end
        ).all()

        if near_deadline_tasks:
            if not self._notification_exists_today(user_id, "near_deadline"):
                task_ids = [t.id for t in near_deadline_tasks]
                notification = Notification(
                    user_id=user_id,
                    title=f"Bạn có {len(near_deadline_tasks)} công việc sắp tới hạn",
                    message=f"Phát hiện {len(near_deadline_tasks)} công việc sẽ tới hạn trong 2 ngày tới. Hãy sắp xếp thời gian hợp lý.",
                    type="warning",
                    severity="warning",
                    source="notification_engine",
                    metadata_json={
                        "notification_type": "near_deadline",
                        "near_deadline_task_ids": task_ids,
                        "near_deadline_count": len(near_deadline_tasks)
                    },
                    is_ai_generated=False
                )
                self.db.add(notification)
                self.db.commit()

    def _check_blocked_tasks(self, user_id: int):
        """Alert: User has blocked tasks"""
        blocked_tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.BLOCKED
        ).all()

        if blocked_tasks:
            if not self._notification_exists_today(user_id, "blocked_task"):
                task_ids = [t.id for t in blocked_tasks]
                notification = Notification(
                    user_id=user_id,
                    title=f"Bạn có {len(blocked_tasks)} công việc bị chặn",
                    message=f"Phát hiện {len(blocked_tasks)} công việc đang bị chặn. Vui lòng kiểm tra và xử lý nguyên nhân.",
                    type="warning",
                    severity="warning",
                    source="notification_engine",
                    metadata_json={
                        "notification_type": "blocked_task",
                        "blocked_task_ids": task_ids,
                        "blocked_count": len(blocked_tasks)
                    },
                    is_ai_generated=False
                )
                self.db.add(notification)
                self.db.commit()

    def _check_low_kpi(self, user_id: int):
        """Alert: User KPI is below 70"""
        snapshot = self.db.query(KpiSnapshot).filter(
            KpiSnapshot.user_id == user_id,
            KpiSnapshot.period_key == self.period_key
        ).first()

        if snapshot and snapshot.total_score < 70:
            if not self._notification_exists_today(user_id, "low_kpi"):
                notification = Notification(
                    user_id=user_id,
                    title="KPI tháng này thấp hơn 70",
                    message=f"Điểm KPI tháng này của bạn là {snapshot.total_score:.1f}, thấp hơn ngưỡng 70. Hãy tập trung hoàn thành công việc và cải thiện hiệu suất.",
                    type="warning",
                    severity="warning",
                    source="notification_engine",
                    metadata_json={
                        "notification_type": "low_kpi",
                        "kpi_score": snapshot.total_score,
                        "period_key": self.period_key
                    },
                    is_ai_generated=False
                )
                self.db.add(notification)
                self.db.commit()

    def _check_excellent_performance(self, user_id: int):
        """Alert: User is excellent performer (high KPI, no overdue, completed many tasks)"""
        snapshot = self.db.query(KpiSnapshot).filter(
            KpiSnapshot.user_id == user_id,
            KpiSnapshot.period_key == self.period_key
        ).first()

        if snapshot and snapshot.total_score >= 85 and snapshot.tasks_overdue == 0:
            # Only alert once per period
            existing = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.metadata_json["notification_type"].astext == "excellent_performance",
                Notification.metadata_json["period_key"].astext == self.period_key,
            ).first()

            if not existing:
                notification = Notification(
                    user_id=user_id,
                    title="Bạn là nhân viên xuất sắc",
                    message=f"Bạn đạt KPI {snapshot.total_score:.1f} và không có công việc quá hạn. Hãy tiếp tục duy trì kết quả này.",
                    type="success",
                    severity="success",
                    source="notification_engine",
                    metadata_json={
                        "notification_type": "excellent_performance",
                        "period_key": self.period_key,
                        "kpi_score": snapshot.total_score,
                        "tasks_completed": snapshot.tasks_completed,
                        "tasks_overdue": snapshot.tasks_overdue
                    },
                    is_ai_generated=False
                )
                self.db.add(notification)
                self.db.commit()

    def _notification_exists_today(self, user_id: int, notification_type: str) -> bool:
        """Check if a notification of the same type already exists for today"""
        today_start, tomorrow_start = business_day_utc_range(self.today)

        existing = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.created_at >= today_start,
            Notification.created_at < tomorrow_start,
            Notification.metadata_json["notification_type"].astext == notification_type,
        ).first()

        return existing is not None
