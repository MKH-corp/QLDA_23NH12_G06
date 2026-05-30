from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, UTC
from app.models.notification import Notification
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.kpi_snapshot import KpiSnapshot
from app.models.department import Department


class NotificationEngine:
    """Rule-based notification engine for automatic alerts"""

    def __init__(self, db: Session):
        self.db = db
        self.today = datetime.now(UTC).date()
        self.period_key = f"{datetime.now().year}-{datetime.now().month:02d}"

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
                    title=f"Ban co {len(overdue_tasks)} cong viec da qua han",
                    message=f"Phat hien {len(overdue_tasks)} task chưa hoàn thành đã vượt quá deadline. Vui lòng ưu tiên hoàn thành các task này.",
                    type="danger",
                    severity="danger",
                    source="notification_engine",
                    metadata_json={
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
                    title=f"Ban co {len(near_deadline_tasks)} cong viec sap toi han",
                    message=f"Phat hien {len(near_deadline_tasks)} task sẽ đến deadline trong 2 ngày tới. Hãy sắp xếp thời gian hợp lý.",
                    type="warning",
                    severity="warning",
                    source="notification_engine",
                    metadata_json={
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
                    title=f"Ban co {len(blocked_tasks)} cong viec bi chan",
                    message=f"Phat hien {len(blocked_tasks)} task đang ở trạng thái blocked. Vui lòng kiểm tra và xử lý các vấn đề để tiếp tục công việc.",
                    type="warning",
                    severity="warning",
                    source="notification_engine",
                    metadata_json={
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
                    title="KPI thang nay thap hon 70",
                    message=f"Diem KPI tháng này của bạn là {snapshot.total_score:.1f}, thấp hơn ngưỡng 70. Hãy tập trung hoàn thành các task và cải thiện hiệu suất.",
                    type="warning",
                    severity="warning",
                    source="notification_engine",
                    metadata_json={
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
            ).first()

            if not existing:
                notification = Notification(
                    user_id=user_id,
                    title="Ban la nhan vien xuat sac",
                    message=f"Ban da tro thanh nhan vien xuat sac voi KPI {snapshot.total_score:.1f} va 0 task qua han. Chuc mung! Hay tiep tuc giu vung thanh tich nay.",
                    type="success",
                    severity="success",
                    source="notification_engine",
                    metadata_json={
                        "notification_type": "excellent_performance",
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
        today_start = datetime.combine(self.today, datetime.min.time())
        today_end = datetime.combine(self.today, datetime.max.time())

        # Map notification_type to a message pattern to find existing notifications
        type_patterns = {
            "overdue_task": "qua han",
            "near_deadline": "sap toi han",
            "blocked_task": "bi chan",
            "low_kpi": "KPI thang nay thap",
            "excellent_performance": "xuat sac"
        }

        pattern = type_patterns.get(notification_type, "")
        if not pattern:
            return False

        existing = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.created_at >= today_start,
            Notification.message.contains(pattern)
        ).first()

        return existing is not None
