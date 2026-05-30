from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.activity import ActivityLog
from app.models.department import Department
from app.models.kpi_snapshot import KpiSnapshot
from app.models.task import Task
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    ActivityLogResponse,
    DashboardResponse,
    DashboardStats,
    DepartmentPerformance,
    UserPerformance,
)
from app.utils.task_ultis import business_period_key


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_data(self, actor: User) -> DashboardResponse:
        period_key = business_period_key()

        users_query = self.db.query(User).filter(User.is_active == True)
        departments_query = self.db.query(Department)
        tasks_query = self.db.query(Task)
        snapshots_query = (
            self.db.query(KpiSnapshot)
            .join(User, KpiSnapshot.user_id == User.id)
            .filter(KpiSnapshot.period_key == period_key, User.is_active == True)
        )

        if actor.role == UserRole.MANAGER:
            users_query = users_query.filter(User.department_id == actor.department_id)
            departments_query = departments_query.filter(Department.id == actor.department_id)
            tasks_query = tasks_query.filter(Task.department_id == actor.department_id)
            snapshots_query = snapshots_query.filter(User.department_id == actor.department_id)

        users = users_query.all()
        departments = departments_query.all()
        snapshots = snapshots_query.all()
        completed_tasks = tasks_query.filter(Task.status == "done").count()
        avg_kpi = round(sum(item.total_score for item in snapshots) / len(snapshots), 1) if snapshots else 0

        department_charts = [
            DepartmentPerformance(
                id=department.id,
                name=department.name,
                score=self._department_score(department.id, period_key),
            )
            for department in departments
        ]

        top_performers_query = (
            self.db.query(KpiSnapshot, User)
            .join(User, KpiSnapshot.user_id == User.id)
            .filter(KpiSnapshot.period_key == period_key, User.is_active == True)
        )
        if actor.role == UserRole.MANAGER:
            top_performers_query = top_performers_query.filter(User.department_id == actor.department_id)

        department_names = {department.id: department.name for department in departments}
        top_performers = [
            UserPerformance(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                department_name=department_names.get(user.department_id, "Unknown"),
                tasks_completed=snapshot.tasks_completed,
                kpi_score=round(snapshot.total_score, 1),
            )
            for snapshot, user in top_performers_query.order_by(KpiSnapshot.total_score.desc()).limit(5).all()
        ]

        recent_activities_query = self.db.query(ActivityLog)
        if actor.role == UserRole.MANAGER:
            recent_activities_query = (
                recent_activities_query
                .join(User, ActivityLog.user_id == User.id)
                .filter(User.department_id == actor.department_id)
            )
        recent_activities = [
            ActivityLogResponse(
                id=log.id,
                action=log.action_type,
                description=log.description,
                time_ago=self._format_time_ago(log.created_at),
            )
            for log in recent_activities_query.order_by(ActivityLog.created_at.desc()).limit(5).all()
        ]

        best_department = max(department_charts, key=lambda item: item.score) if department_charts else None
        insights = (
            f"Nang suat trung binh dat {avg_kpi}%. "
            f"Phong {best_department.name if best_department else 'N/A'} dang co hieu suat cao nhat."
        )

        return DashboardResponse(
            stats=DashboardStats(
                total_employees=len(users),
                active_departments=len(departments),
                completed_tasks=completed_tasks,
                avg_kpi=avg_kpi,
            ),
            department_charts=department_charts,
            top_performers=top_performers,
            recent_activities=recent_activities,
            ai_insights=insights,
        )

    def _department_score(self, department_id: int, period_key: str) -> float:
        snapshots = (
            self.db.query(KpiSnapshot)
            .join(User, KpiSnapshot.user_id == User.id)
            .filter(
                User.department_id == department_id,
                User.is_active == True,
                KpiSnapshot.period_key == period_key,
            )
            .all()
        )
        return round(sum(item.total_score for item in snapshots) / len(snapshots), 1) if snapshots else 0

    @staticmethod
    def _format_time_ago(created_at: datetime | None) -> str:
        if created_at is None:
            return ""
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            return f"{int(seconds // 60)} mins ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        return f"{int(seconds // 86400)} days ago"
