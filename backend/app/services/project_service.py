"""
ProjectService — toàn bộ business logic ở đây, router chỉ gọi service.

Nguyên tắc:
- validate status transition trước khi đổi
- ghi audit log cho mọi field thay đổi
- ghi status history khi đổi status
- trigger activity log (global)
- trigger KPI recalculation khi project COMPLETED
- trigger progress recalculation sau mọi thay đổi task/milestone
- phân quyền: admin > manager > project_manager > member > viewer
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import (
    ALLOWED_TRANSITIONS, Project, ProjectAuditLog,
    ProjectMember, ProjectMemberRole, ProjectMilestone,
    ProjectStatus, ProjectStatusHistory,
)
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    AddMemberRequest, AuditLogRead, MilestoneCreate, MilestoneRead,
    ProjectAnalytics, ProjectCreate, ProjectKpiContribution,
    ProjectListItem, ProjectMemberRead, ProjectOverview,
    StatusHistoryRead, TaskSummary, UpdateMemberRoleRequest,
    ProjectUpdate,
)
from app.services.project_progress_engine import ProjectProgressEngine
from app.utils.logger import log_system_activity


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db   = db
        self.repo = ProjectRepository(db)

    # ═══════════════════════════════════════════════════════════════════
    # Project CRUD
    # ═══════════════════════════════════════════════════════════════════

    def list_projects(self, actor: User, department_id: int | None = None,
                      status: str | None = None, skip: int = 0, limit: int = 50
                      ) -> list[ProjectListItem]:
        """Lấy danh sách project theo quyền."""
        if actor.role == UserRole.STAFF:
            projects = self.repo.get_projects_for_member(actor.id)
        elif actor.role == UserRole.MANAGER:
            projects = self.repo.list(
                department_id=actor.department_id, status=status,
                skip=skip, limit=limit,
            )
        else:  # ADMIN
            projects = self.repo.list(
                department_id=department_id, status=status,
                skip=skip, limit=limit,
            )

        return [self._to_list_item(p) for p in projects]

    def create_project(self, payload: ProjectCreate, actor: User) -> ProjectListItem:
        if actor.role == UserRole.STAFF:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Staff không được tạo project")

        # Auto-generate code nếu không truyền
        code = payload.code or self._generate_code(payload.name)

        project = Project(
            name=payload.name, code=code,
            description=payload.description,
            status=ProjectStatus.PLANNING.value,
            priority=payload.priority,
            department_id=payload.department_id or actor.department_id,
            manager_id=payload.manager_id,
            start_date=payload.start_date, end_date=payload.end_date,
            estimated_hours=payload.estimated_hours,
            estimated_budget=payload.estimated_budget,
            created_by=actor.id, updated_by=actor.id,
        )
        project = self.repo.create(project)

        # Tự động thêm người tạo làm PROJECT_MANAGER
        self._add_member_internal(project.id, actor.id,
                                  ProjectMemberRole.PROJECT_MANAGER, actor.id)

        # Ghi status history khởi đầu
        self._write_status_history(project.id, None,
                                   ProjectStatus.PLANNING.value, actor.id,
                                   "Project được tạo mới")

        # Activity log
        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="CREATE", entity_type="PROJECT", entity_id=project.id,
            description=f"Tạo project mới: {project.name}",
        )
        return self._to_list_item(project)

    def get_project_overview(self, project_id: int, actor: User) -> ProjectOverview:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)

        # Reload full để có đủ relationships
        project = self.repo.get_by_id_full(project_id)
        counts  = self.repo.get_task_counts(project_id)
        tasks   = self.repo.get_recent_tasks(project_id, limit=10)
        engine  = ProjectProgressEngine(self.db)

        analytics = self._build_analytics(project, counts, engine)
        kpi       = self._build_kpi_contribution(project_id)

        return ProjectOverview(
            id=project.id, name=project.name, code=project.code,
            description=project.description, status=project.status,
            priority=project.priority.value if project.priority else "MEDIUM",
            progress_percentage=project.progress_percentage,
            start_date=project.start_date, end_date=project.end_date,
            estimated_hours=project.estimated_hours,
            actual_hours=project.actual_hours or 0,
            estimated_budget=project.estimated_budget,
            department_name=project.department.name if project.department else "",
            manager_name=project.manager.full_name if project.manager else "",
            created_at=project.created_at, updated_at=project.updated_at,
            members=[ProjectMemberRead.from_member(m) for m in project.members],
            milestones=[MilestoneRead.model_validate(m) for m in project.milestones],
            recent_tasks=[self._task_to_summary(t) for t in tasks],
            status_history=[StatusHistoryRead.from_history(h)
                            for h in project.status_history[:10]],
            recent_audit_logs=[AuditLogRead.from_audit(a)
                               for a in project.audit_logs[:20]],
            analytics=analytics,
            kpi_contribution=kpi,
        )

    def update_project(self, project_id: int, payload: ProjectUpdate,
                       actor: User) -> ProjectListItem:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)

        data = payload.model_dump(exclude_unset=True)
        reason = data.pop("reason", None)

        auditable_fields = [
            "name", "code", "description", "priority",
            "start_date", "end_date", "estimated_hours",
            "estimated_budget", "department_id", "manager_id",
        ]

        for field in auditable_fields:
            if field in data:
                old_val = str(getattr(project, field, None))
                new_val = str(data[field])
                if old_val != new_val:
                    self._write_audit_log(project_id, actor.id,
                                          field, old_val, new_val)

        # Xử lý đổi status riêng (validate transition)
        if "status" in data:
            new_status = ProjectStatus(data["status"])
            if new_status.value != project.status:
                self._validate_transition(project, new_status)
                old_status = project.status
                project.status = new_status.value
                self._write_status_history(project_id, old_status,
                                           new_status.value, actor.id, reason)

                # Archive
                if new_status == ProjectStatus.ARCHIVED:
                    project.archived_at = datetime.now(timezone.utc)

                # KPI trigger khi COMPLETED
                if new_status == ProjectStatus.COMPLETED:
                    self._trigger_completion_kpi(project_id, actor)

            data.pop("status")

        for field, value in data.items():
            setattr(project, field, value)

        project.updated_by = actor.id
        project = self.repo.update(project)

        # Recalculate progress
        ProjectProgressEngine(self.db).calculate(project)

        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="UPDATE", entity_type="PROJECT", entity_id=project.id,
            description=f"Cập nhật project: {project.name}",
        )
        return self._to_list_item(project)

    def delete_project(self, project_id: int, actor: User) -> None:
        if actor.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Chỉ Admin mới được xóa project")
        project = self._get_project_or_404(project_id)
        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="DELETE", entity_type="PROJECT", entity_id=project_id,
            description=f"Xóa project: {project.name}",
        )
        self.repo.delete(project)

    # ═══════════════════════════════════════════════════════════════════
    # Member Management
    # ═══════════════════════════════════════════════════════════════════

    def add_member(self, project_id: int, req: AddMemberRequest,
                   actor: User) -> ProjectMemberRead:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)

        existing = self.repo.get_member(project_id, req.user_id)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                "Người dùng đã là thành viên của project này")

        member = self._add_member_internal(project_id, req.user_id,
                                           req.role, actor.id)

        self._write_audit_log(project_id, actor.id, "members",
                              None, f"Thêm user_id={req.user_id} role={req.role.value}")
        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="UPDATE", entity_type="PROJECT", entity_id=project_id,
            description=f"Thêm thành viên vào project {project.name}",
        )
        # reload để lấy user info
        member = self.repo.get_member(project_id, req.user_id)
        return ProjectMemberRead.from_member(member)

    def remove_member(self, project_id: int, user_id: int, actor: User) -> None:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)

        member = self.repo.get_member(project_id, user_id)
        if not member:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                "Không tìm thấy thành viên")

        self._write_audit_log(project_id, actor.id, "members",
                              f"user_id={user_id}", None)
        self.repo.remove_member(member)

    def update_member_role(self, project_id: int, user_id: int,
                           req: UpdateMemberRoleRequest, actor: User
                           ) -> ProjectMemberRead:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)

        member = self.repo.get_member(project_id, user_id)
        if not member:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                "Không tìm thấy thành viên")

        self._write_audit_log(project_id, actor.id, "member_role",
                              member.role.value, req.role.value)
        member.role = req.role
        self.repo.update_member(member)
        return ProjectMemberRead.from_member(member)

    # ═══════════════════════════════════════════════════════════════════
    # Milestone Management
    # ═══════════════════════════════════════════════════════════════════

    def create_milestone(self, project_id: int, payload: MilestoneCreate,
                         actor: User) -> MilestoneRead:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)

        milestone = ProjectMilestone(
            project_id=project_id,
            title=payload.title, description=payload.description,
            due_date=payload.due_date, weight=payload.weight,
            created_by=actor.id,
        )
        milestone = self.repo.create_milestone(milestone)
        ProjectProgressEngine(self.db).calculate(project)

        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="CREATE", entity_type="PROJECT", entity_id=project_id,
            description=f"Tạo milestone '{milestone.title}' cho project {project.name}",
        )
        return MilestoneRead.model_validate(milestone)

    def complete_milestone(self, project_id: int, milestone_id: int,
                           actor: User) -> MilestoneRead:
        project   = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)

        milestone = self.repo.get_milestone(milestone_id)
        if not milestone or milestone.project_id != project_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone không tồn tại")
        if milestone.is_completed:
            raise HTTPException(status.HTTP_409_CONFLICT, "Milestone đã hoàn thành")

        milestone.is_completed = True
        milestone.completed_at = datetime.now(timezone.utc)
        self.repo.update_milestone(milestone)

        # Recalculate progress
        ProjectProgressEngine(self.db).calculate(project)

        # KPI bonus cho project manager khi hoàn thành milestone quan trọng
        if milestone.weight >= 3:
            self._trigger_milestone_kpi_bonus(project_id, actor)

        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="COMPLETE", entity_type="PROJECT", entity_id=project_id,
            description=f"Hoàn thành milestone '{milestone.title}'",
        )
        return MilestoneRead.model_validate(milestone)

    # ═══════════════════════════════════════════════════════════════════
    # Analytics
    # ═══════════════════════════════════════════════════════════════════

    def get_analytics(self, project_id: int, actor: User) -> ProjectAnalytics:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)
        counts  = self.repo.get_task_counts(project_id)
        engine  = ProjectProgressEngine(self.db)
        return self._build_analytics(project, counts, engine)

    def get_dashboard_analytics(self, actor: User) -> dict:
        """Analytics tổng quan toàn bộ project — dùng cho dashboard."""
        if actor.role == UserRole.STAFF:
            projects = self.repo.get_projects_for_member(actor.id)
        elif actor.role == UserRole.MANAGER:
            projects = self.repo.list(department_id=actor.department_id, limit=200)
        else:
            projects = self.repo.list(limit=200)

        status_counts = {}
        for p in projects:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1

        overdue_projects = [
            p for p in projects
            if p.end_date and p.end_date < date.today()
            and p.status not in ("COMPLETED", "CANCELLED", "ARCHIVED")
        ]
        avg_progress = (
            sum(p.progress_percentage for p in projects) / len(projects)
            if projects else 0
        )
        return {
            "total_projects":    len(projects),
            "status_breakdown":  status_counts,
            "overdue_projects":  len(overdue_projects),
            "avg_progress":      round(avg_progress, 1),
            "active_projects":   status_counts.get("ACTIVE", 0),
        }

    # ═══════════════════════════════════════════════════════════════════
    # Private helpers
    # ═══════════════════════════════════════════════════════════════════

    def _get_project_or_404(self, project_id: int) -> Project:
        project = self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project không tồn tại")
        return project

    def _check_read_access(self, project: Project, actor: User) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.MANAGER and project.department_id == actor.department_id:
            return
        # Staff/PM: chỉ xem project mình là thành viên
        member = self.repo.get_member(project.id, actor.id)
        if not member and project.manager_id != actor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Không có quyền xem project này")

    def _check_write_access(self, project: Project, actor: User) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.MANAGER and project.department_id == actor.department_id:
            return
        # Project Manager trong project
        member = self.repo.get_member(project.id, actor.id)
        if member and member.role == ProjectMemberRole.PROJECT_MANAGER:
            return
        if project.manager_id == actor.id:
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Không có quyền chỉnh sửa project này")

    def _validate_transition(self, project: Project, new_status: ProjectStatus) -> None:
        try:
            current = ProjectStatus(project.status)
        except ValueError:
            return  # status cũ không hợp lệ, cho phép đổi
        if new_status == current:
            return
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Không thể chuyển từ {current.value} sang {new_status.value}. "
                f"Cho phép: {[s.value for s in allowed]}",
            )

    def _add_member_internal(self, project_id: int, user_id: int,
                              role: ProjectMemberRole, added_by: int
                              ) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id, user_id=user_id,
            role=role, added_by=added_by,
        )
        return self.repo.add_member(member)

    def _write_status_history(self, project_id: int, from_status: str | None,
                               to_status: str, changed_by: int | None,
                               reason: str | None) -> None:
        entry = ProjectStatusHistory(
            project_id=project_id,
            from_status=from_status, to_status=to_status,
            changed_by=changed_by, reason=reason,
        )
        self.repo.add_status_history(entry)

    def _write_audit_log(self, project_id: int, changed_by: int | None,
                          field: str, old_val: str | None, new_val: str | None
                          ) -> None:
        log = ProjectAuditLog(
            project_id=project_id, changed_by=changed_by,
            field_name=field, old_value=old_val, new_value=new_val,
        )
        self.repo.add_audit_log(log)

    def _to_list_item(self, project: Project) -> ProjectListItem:
        counts = self.repo.get_task_counts(project.id)
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id
        ).all()
        member_count = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id
        ).count()
        is_overdue = bool(
            project.end_date and project.end_date < date.today()
            and project.status not in ("COMPLETED", "CANCELLED", "ARCHIVED")
        )
        return ProjectListItem(
            id=project.id, name=project.name, description=project.description,
            code=project.code,
            status=project.status,
            priority=project.priority.value if project.priority else "MEDIUM",
            progress_percentage=project.progress_percentage or 0,
            start_date=project.start_date, end_date=project.end_date,
            department_id=project.department_id, manager_id=project.manager_id,
            department_name=project.department.name if project.department else "",
            manager_name=project.manager.full_name if project.manager else "",
            total_tasks=counts["total"],
            completed_tasks=counts["completed"],
            overdue_tasks=counts["overdue"],
            member_count=member_count,
            milestone_count=len(milestones),
            milestones_done=sum(1 for m in milestones if m.is_completed),
            is_overdue=is_overdue,
        )

    def _build_analytics(self, project: Project, counts: dict,
                          engine: ProjectProgressEngine) -> ProjectAnalytics:
        today       = date.today()
        total       = counts["total"]
        completed   = counts["completed"]
        on_time_tasks = self.db.query(Task).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.DONE,
            Task.deadline.isnot(None),
            Task.done_at.isnot(None),
        ).all()
        on_time_count = sum(
            1 for t in on_time_tasks
            if t.done_at and t.deadline and t.done_at.date() <= t.deadline
        )
        on_time_rate = (on_time_count / completed * 100) if completed else 0

        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id
        ).all()
        ms_total = len(milestones)
        ms_done  = sum(1 for m in milestones if m.is_completed)
        ms_pct   = (ms_done / ms_total * 100) if ms_total else 0

        # Velocity: tasks hoàn thành / số tuần project đã chạy
        weeks_elapsed = 1
        if project.start_date:
            delta = today - project.start_date
            weeks_elapsed = max(1, delta.days // 7)
        velocity = completed / weeks_elapsed

        # Risk indicators
        risk_indicators: list[str] = []
        if counts["overdue"] > 0:
            risk_indicators.append(f"{counts['overdue']} task đã quá hạn")
        if counts["blocked"] > 0:
            risk_indicators.append(f"{counts['blocked']} task đang bị blocked")
        if project.end_date and project.end_date < today and project.status == "ACTIVE":
            risk_indicators.append("Project đã quá deadline")
        if project.progress_percentage < 30 and project.end_date:
            remaining = (project.end_date - today).days
            if remaining < 14:
                risk_indicators.append("Tiến độ thấp, deadline gần")

        n = len(risk_indicators)
        risk_level = "LOW" if n == 0 else "MEDIUM" if n == 1 else "HIGH" if n == 2 else "CRITICAL"

        budget_util = None
        if project.estimated_budget and project.estimated_budget > 0:
            budget_util = round((project.actual_hours or 0) / project.estimated_budget * 100, 1)

        return ProjectAnalytics(
            progress_percentage=project.progress_percentage or 0,
            total_tasks=total, completed_tasks=completed,
            pending_tasks=counts["pending"], doing_tasks=counts["doing"],
            blocked_tasks=counts["blocked"], overdue_tasks=counts["overdue"],
            completion_rate=round(completed / total * 100, 1) if total else 0,
            on_time_rate=round(on_time_rate, 1),
            velocity=round(velocity, 2),
            estimated_hours=project.estimated_hours,
            actual_hours=project.actual_hours or 0,
            budget_utilization=budget_util,
            milestone_progress=round(ms_pct, 1),
            risk_level=risk_level,
            risk_indicators=risk_indicators,
        )

    def _build_kpi_contribution(self, project_id: int) -> ProjectKpiContribution:
        from app.models.kpi_snapshot import KpiSnapshot
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

        contributions = []
        total_score = 0.0
        for m in members:
            snap = self.db.query(KpiSnapshot).filter(
                KpiSnapshot.user_id == m.user_id
            ).order_by(KpiSnapshot.period_key.desc()).first()
            score = snap.total_score if snap else 0
            total_score += score
            contributions.append({
                "user_id":   m.user_id,
                "full_name": m.user.full_name if m.user else "",
                "role":      m.role.value,
                "kpi_score": score,
            })

        tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
        completed = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        overdue   = sum(
            1 for t in tasks
            if t.status != TaskStatus.DONE and t.deadline and t.deadline < date.today()
        )
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).all()
        ms_done = sum(1 for m in milestones if m.is_completed)

        return ProjectKpiContribution(
            total_score_contributed=round(total_score, 2),
            tasks_completed=completed,
            tasks_overdue=overdue,
            milestones_completed=ms_done,
            on_time_rate=0,
            member_contributions=contributions,
        )

    def _trigger_completion_kpi(self, project_id: int, actor: User) -> None:
        """Khi project COMPLETED → recalculate KPI cho tất cả thành viên."""
        from app.services.kpi_engine import KpiEngine
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()
        engine = KpiEngine(self.db)
        for m in members:
            try:
                engine.recalculate_monthly_kpi(m.user_id)
            except Exception:
                pass  # không để lỗi KPI crash luồng chính

    def _trigger_milestone_kpi_bonus(self, project_id: int, actor: User) -> None:
        """Milestone quan trọng (weight >= 3) → recalculate KPI manager."""
        from app.services.kpi_engine import KpiEngine
        project = self.repo.get_by_id(project_id)
        if project and project.manager_id:
            try:
                KpiEngine(self.db).recalculate_monthly_kpi(project.manager_id)
            except Exception:
                pass

    def _task_to_summary(self, task: Task) -> TaskSummary:
        today = date.today()
        from app.utils.task_ultis import infer_priority
        return TaskSummary(
            id=task.id, title=task.title, status=task.status,
            priority=infer_priority(task.base_weight),
            deadline=task.deadline,
            assignee_name=task.assignee.full_name if task.assignee else "",
            is_overdue=bool(
                task.status != "done" and task.deadline and task.deadline < today
            ),
        )

    @staticmethod
    def _generate_code(name: str) -> str:
        import re, time
        prefix = re.sub(r"[^A-Za-z0-9]", "", name[:6]).upper() or "PRJ"
        return f"{prefix}-{int(time.time()) % 100000}"
