from datetime import datetime, timezone

from sqlalchemy import and_, func
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
        snapshot_stats_query = (
            self.db.query(
                func.count(KpiSnapshot.id),
                func.coalesce(func.avg(KpiSnapshot.total_score), 0),
            )
            .join(User, KpiSnapshot.user_id == User.id)
            .filter(KpiSnapshot.period_key == period_key, User.is_active == True)
        )

        if actor.role == UserRole.MANAGER:
            users_query = users_query.filter(User.department_id == actor.department_id)
            departments_query = departments_query.filter(Department.id == actor.department_id)
            tasks_query = tasks_query.filter(Task.department_id == actor.department_id)
            snapshot_stats_query = snapshot_stats_query.filter(User.department_id == actor.department_id)

        total_employees = users_query.count()
        departments = departments_query.all()
        completed_tasks = tasks_query.filter(Task.status == "done").count()
        _, avg_kpi_value = snapshot_stats_query.one()
        avg_kpi = round(float(avg_kpi_value), 1)

        department_scores_query = (
            self.db.query(
                Department.id,
                Department.name,
                func.coalesce(func.avg(KpiSnapshot.total_score), 0),
            )
            .outerjoin(User, and_(User.department_id == Department.id, User.is_active == True))
            .outerjoin(
                KpiSnapshot,
                and_(KpiSnapshot.user_id == User.id, KpiSnapshot.period_key == period_key),
            )
        )
        if actor.role == UserRole.MANAGER:
            department_scores_query = department_scores_query.filter(Department.id == actor.department_id)
        department_charts = [
            DepartmentPerformance(
                id=department_id,
                name=department_name,
                score=round(float(score), 1),
            )
            for department_id, department_name, score in department_scores_query.group_by(Department.id, Department.name).all()
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
            f"Năng suất trung bình đạt {avg_kpi}%. "
            f"Phòng {best_department.name if best_department else 'N/A'} đang có hiệu suất cao nhất."
        )

        return DashboardResponse(
            stats=DashboardStats(
                total_employees=total_employees,
                active_departments=len(departments),
                completed_tasks=completed_tasks,
                avg_kpi=avg_kpi,
            ),
            department_charts=department_charts,
            top_performers=top_performers,
            recent_activities=recent_activities,
            ai_insights=insights,
        )

    @staticmethod
    def _format_time_ago(created_at: datetime | None) -> str:
        if created_at is None:
            return ""
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
        if seconds < 60:
            return "Vừa xong"
        if seconds < 3600:
            return f"{int(seconds // 60)} phút trước"
        if seconds < 86400:
            return f"{int(seconds // 3600)} giờ trước"
        return f"{int(seconds // 86400)} ngày trước"
