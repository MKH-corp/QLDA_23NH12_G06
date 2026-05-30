from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.models.kpi_snapshot import KpiSnapshot
from app.models.notification import Notification
from app.models.department import Department


class AIContextService:
    """Service to gather context from database for AI analysis"""

    def __init__(self, db: Session):
        self.db = db
        self.today = datetime.now(UTC).date()
        self.period_key = f"{datetime.now().year}-{datetime.now().month:02d}"

    def get_context_for_user(self, current_user: User) -> dict:
        """Get AI context for a user based on their role and permissions"""
        context = {
            "user_id": current_user.id,
            "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
            "department_id": current_user.department_id,
            "period_key": self.period_key,
        }

        if current_user.role == UserRole.STAFF:
            # Staff: get own data
            context.update(self._get_user_context(current_user.id))
        elif current_user.role == UserRole.MANAGER:
            # Manager: get team data
            context.update(self._get_team_context(current_user.department_id))
        else:
            # Admin: get system-wide data
            context.update(self._get_system_context())

        return context

    def _get_user_context(self, user_id: int) -> dict:
        """Get individual user context"""
        # User tasks
        all_tasks = self.db.query(Task).filter(Task.assignee_id == user_id).all()

        overdue_tasks = [t for t in all_tasks if t.status != TaskStatus.DONE and t.deadline and t.deadline < self.today]
        near_deadline_tasks = [t for t in all_tasks if t.status != TaskStatus.DONE and t.deadline and
                               self.today <= t.deadline <= self.today + timedelta(days=2)]
        blocked_tasks = [t for t in all_tasks if t.status == TaskStatus.BLOCKED]
        done_tasks = [t for t in all_tasks if t.status == TaskStatus.DONE]

        # KPI
        snapshot = self.db.query(KpiSnapshot).filter(
            KpiSnapshot.user_id == user_id,
            KpiSnapshot.period_key == self.period_key
        ).first()

        # Recent notifications
        recent_notifs = self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(10).all()

        return {
            "own_tasks": len(all_tasks),
            "own_done_tasks": len(done_tasks),
            "own_overdue_tasks": len(overdue_tasks),
            "own_overdue_task_ids": [t.id for t in overdue_tasks],
            "own_near_deadline_tasks": len(near_deadline_tasks),
            "own_near_deadline_task_ids": [t.id for t in near_deadline_tasks],
            "own_blocked_tasks": len(blocked_tasks),
            "own_blocked_task_ids": [t.id for t in blocked_tasks],
            "own_kpi_score": snapshot.total_score if snapshot else 0,
            "own_kpi_snapshot": {
                "tasks_completed": snapshot.tasks_completed,
                "tasks_overdue": snapshot.tasks_overdue,
                "breakdown": snapshot.breakdown
            } if snapshot else None,
            "recent_notifications": len(recent_notifs),
        }

    def _get_team_context(self, department_id: int) -> dict:
        """Get team/department context for manager"""
        team_users = self.db.query(User).filter(
            User.department_id == department_id,
            User.is_active == True
        ).all()

        team_kpis = []
        risk_users = []
        top_performers = []
        team_overdue = 0
        team_tasks_done = 0

        for user in team_users:
            snapshot = self.db.query(KpiSnapshot).filter(
                KpiSnapshot.user_id == user.id,
                KpiSnapshot.period_key == self.period_key
            ).first()

            if snapshot:
                team_kpis.append(snapshot.total_score)
                team_tasks_done += snapshot.tasks_completed
                team_overdue += snapshot.tasks_overdue

                if snapshot.total_score < 70:
                    risk_users.append({
                        "user_id": user.id,
                        "name": user.full_name,
                        "kpi": snapshot.total_score,
                        "overdue": snapshot.tasks_overdue
                    })
                elif snapshot.total_score >= 85:
                    top_performers.append({
                        "user_id": user.id,
                        "name": user.full_name,
                        "kpi": snapshot.total_score
                    })

        avg_team_kpi = sum(team_kpis) / len(team_kpis) if team_kpis else 0

        return {
            "team_size": len(team_users),
            "team_avg_kpi": avg_team_kpi,
            "team_tasks_done": team_tasks_done,
            "team_overdue": team_overdue,
            "risk_users": risk_users,
            "top_performers": top_performers,
            "team_users": [{"id": u.id, "name": u.full_name, "email": u.email} for u in team_users],
        }

    def _get_system_context(self) -> dict:
        """Get system-wide context for admin"""
        all_users = self.db.query(User).filter(User.is_active == True).all()
        all_depts = self.db.query(Department).all()

        all_kpis = []
        risk_users = []
        top_performers = []
        system_overdue = 0
        system_tasks_done = 0

        for user in all_users:
            snapshot = self.db.query(KpiSnapshot).filter(
                KpiSnapshot.user_id == user.id,
                KpiSnapshot.period_key == self.period_key
            ).first()

            if snapshot:
                all_kpis.append(snapshot.total_score)
                system_tasks_done += snapshot.tasks_completed
                system_overdue += snapshot.tasks_overdue

                if snapshot.total_score < 70:
                    risk_users.append({
                        "user_id": user.id,
                        "name": user.full_name,
                        "kpi": snapshot.total_score,
                        "department": user.department.name if user.department else "N/A"
                    })
                elif snapshot.total_score >= 85:
                    top_performers.append({
                        "user_id": user.id,
                        "name": user.full_name,
                        "kpi": snapshot.total_score,
                        "department": user.department.name if user.department else "N/A"
                    })

        avg_system_kpi = sum(all_kpis) / len(all_kpis) if all_kpis else 0

        return {
            "total_users": len(all_users),
            "total_departments": len(all_depts),
            "system_avg_kpi": avg_system_kpi,
            "system_tasks_done": system_tasks_done,
            "system_overdue": system_overdue,
            "risk_users": risk_users,
            "top_performers": top_performers,
        }
