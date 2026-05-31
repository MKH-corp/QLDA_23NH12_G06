"""
ProjectRepository — tất cả query được tối ưu:
- joinedload để tránh N+1
- aggregation bằng subquery thay vì loop Python
- index-friendly filters
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.project import (
    Project, ProjectAuditLog, ProjectMember,
    ProjectMilestone, ProjectStatusHistory,
)
from app.models.task import Task, TaskStatus
from app.utils.task_ultis import business_today


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Project CRUD ───────────────────────────────────────────────────

    def create(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> Project | None:
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.department),
                joinedload(Project.manager),
                joinedload(Project.creator),
            )
            .filter(Project.id == project_id)
            .first()
        )

    def get_by_id_full(self, project_id: int) -> Project | None:
        """Load toàn bộ relationships cho detail page — 1 query duy nhất."""
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.department),
                joinedload(Project.manager),
                joinedload(Project.creator),
                selectinload(Project.members).joinedload(ProjectMember.user),
                selectinload(Project.milestones),
                selectinload(Project.status_history).joinedload(ProjectStatusHistory.actor),
                selectinload(Project.audit_logs).joinedload(ProjectAuditLog.actor),
            )
            .filter(Project.id == project_id)
            .first()
        )

    def list(
        self,
        department_id: int | None = None,
        status: str | None = None,
        manager_id: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Project]:
        q = (
            self.db.query(Project)
            .options(
                joinedload(Project.department),
                joinedload(Project.manager),
            )
            .order_by(Project.created_at.desc())
        )
        if department_id:
            q = q.filter(Project.department_id == department_id)
        if status:
            q = q.filter(Project.status == status)
        if manager_id:
            q = q.filter(Project.manager_id == manager_id)
        return q.offset(skip).limit(limit).all()

    def update(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()

    # ── Task aggregation (dùng subquery, không loop) ────────────────────

    def get_task_counts(self, project_id: int) -> dict:
        """
        Trả về dict với total/completed/doing/pending/blocked/overdue tasks.
        Dùng 1 query group-by thay vì nhiều query riêng lẻ.
        """
        rows = (
            self.db.query(Task.status, func.count(Task.id))
            .filter(Task.project_id == project_id)
            .group_by(Task.status)
            .all()
        )
        counts: dict[str, int] = {
            (r[0].value if hasattr(r[0], "value") else r[0]): r[1]
            for r in rows
        }
        total     = sum(counts.values())
        completed = counts.get("done", 0)
        doing     = counts.get("doing", 0)
        review    = counts.get("in_review", 0)
        blocked   = counts.get("blocked", 0)
        pending   = counts.get("todo", 0)

        overdue = (
            self.db.query(func.count(Task.id))
            .filter(
                Task.project_id == project_id,
                Task.status != TaskStatus.DONE,
                Task.deadline.isnot(None),
                Task.deadline < business_today(),
            )
            .scalar() or 0
        )
        return dict(
            total=total, completed=completed, doing=doing, review=review,
            blocked=blocked, pending=pending, overdue=overdue,
        )

    def get_recent_tasks(self, project_id: int, limit: int = 10) -> list[Task]:
        from sqlalchemy.orm import joinedload as jl
        return (
            self.db.query(Task)
            .options(jl(Task.assignee))
            .filter(Task.project_id == project_id)
            .order_by(Task.id.desc())
            .limit(limit)
            .all()
        )

    # ── Member management ───────────────────────────────────────────────

    def get_member(self, project_id: int, user_id: int) -> ProjectMember | None:
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .first()
        )

    def list_members(self, project_id: int, active_only: bool = False) -> list[ProjectMember]:
        query = (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.user))
            .filter(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.role.asc(), ProjectMember.joined_at.asc())
        )
        if active_only:
            query = query.filter(ProjectMember.is_active == True)
        return query.all()

    def add_member(self, member: ProjectMember) -> ProjectMember:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, member: ProjectMember) -> None:
        member.is_active = False
        self.db.add(member)
        self.db.commit()

    def update_member(self, member: ProjectMember) -> ProjectMember:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    # ── Milestone management ────────────────────────────────────────────

    def create_milestone(self, milestone: ProjectMilestone) -> ProjectMilestone:
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def get_milestone(self, milestone_id: int) -> ProjectMilestone | None:
        return self.db.get(ProjectMilestone, milestone_id)

    def update_milestone(self, milestone: ProjectMilestone) -> ProjectMilestone:
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def delete_milestone(self, milestone: ProjectMilestone) -> None:
        self.db.delete(milestone)
        self.db.commit()

    # ── Audit & history ─────────────────────────────────────────────────

    def add_status_history(self, entry: ProjectStatusHistory) -> None:
        self.db.add(entry)
        self.db.commit()

    def add_audit_log(self, log: ProjectAuditLog) -> None:
        self.db.add(log)
        self.db.commit()

    def get_audit_logs(self, project_id: int, limit: int = 50) -> list[ProjectAuditLog]:
        return (
            self.db.query(ProjectAuditLog)
            .options(joinedload(ProjectAuditLog.actor))
            .filter(ProjectAuditLog.project_id == project_id)
            .order_by(ProjectAuditLog.changed_at.desc())
            .limit(limit)
            .all()
        )

    # ── Analytics helpers ───────────────────────────────────────────────

    def count_projects_by_status(self, department_id: int | None = None) -> dict[str, int]:
        q = self.db.query(Project.status, func.count(Project.id)).group_by(Project.status)
        if department_id:
            q = q.filter(Project.department_id == department_id)
        return {row[0]: row[1] for row in q.all()}

    def get_projects_for_member(self, user_id: int) -> list[Project]:
        """Lấy project mà user là thành viên (kể cả manager)."""
        member_project_ids = (
            self.db.query(ProjectMember.project_id)
            .filter(
                ProjectMember.user_id == user_id,
                ProjectMember.is_active == True,
            )
            .subquery()
        )
        return (
            self.db.query(Project)
            .options(joinedload(Project.department))
            .filter(
                (Project.manager_id == user_id) |
                (Project.id.in_(select(member_project_ids)))
            )
            .order_by(Project.created_at.desc())
            .all()
        )
