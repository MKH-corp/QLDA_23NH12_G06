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

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.project import (
    ALLOWED_TRANSITIONS, Project, ProjectAuditLog,
    ProjectMember, ProjectMemberRole, ProjectMilestone,
    ProjectStatus, ProjectStatusHistory,
)
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    AddMemberRequest, AssignableUserRead, AuditLogRead, MilestoneCreate, MilestoneRead,
    MilestoneUpdate,
    ProjectAnalytics, ProjectCreate, ProjectKpiContribution,
    ProjectListItem, ProjectMemberPerformanceRead, ProjectMemberRead,
    ProjectOverview, ProjectReportRead, MyProjectRead,
    StatusHistoryRead, TaskSummary, UpdateMemberRoleRequest,
    ProjectUpdate, TeamWorkloadRead,
)
from app.services.project_progress_engine import ProjectProgressEngine
from app.utils.logger import log_system_activity
from app.utils.task_ultis import business_today, completion_business_date


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db   = db
        self.repo = ProjectRepository(db)

    # ═══════════════════════════════════════════════════════════════════
    # Project CRUD
    # ═══════════════════════════════════════════════════════════════════

    def list_projects(self, actor: User, department_id: int | None = None,
                      status: str | None = None, manager_id: int | None = None,
                      skip: int = 0, limit: int = 50
                      ) -> list[ProjectListItem]:
        """Lấy danh sách project theo quyền."""
        if actor.role == UserRole.STAFF:
            projects = self.repo.get_projects_for_member(actor.id)
        elif actor.role == UserRole.MANAGER:
            projects = self.repo.list_for_manager(
                manager_id=actor.id, department_id=actor.department_id,
                filter_department_id=department_id, filter_manager_id=manager_id,
                status=status,
                skip=skip, limit=limit,
            )
        else:  # ADMIN
            projects = self.repo.list(
                department_id=department_id, status=status, manager_id=manager_id,
                skip=skip, limit=limit,
            )

        return [self._to_list_item(p) for p in projects]

    def create_project(self, payload: ProjectCreate, actor: User) -> ProjectListItem:
        if actor.role == UserRole.STAFF:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Staff không được tạo project")

        # Auto-generate code nếu không truyền
        name = payload.name.strip()
        if not name:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "Project name must not be blank")
        code = payload.code.strip() if payload.code else self._generate_code(name)
        self._ensure_unique_code(code)
        department_id = payload.department_id or actor.department_id
        self._validate_department(department_id)
        if actor.role == UserRole.MANAGER and department_id != actor.department_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Manager cannot create projects outside their department")
        manager_id = payload.manager_id or (actor.id if actor.role == UserRole.MANAGER else None)
        self._validate_project_manager(manager_id, department_id)
        self._validate_project_dates(payload.start_date, payload.end_date)

        project = Project(
            name=name, code=code,
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority,
            department_id=department_id,
            manager_id=manager_id,
            start_date=payload.start_date, end_date=payload.end_date,
            estimated_hours=payload.estimated_hours,
            estimated_budget=payload.estimated_budget,
            project_weight=payload.project_weight,
            created_by=actor.id, updated_by=actor.id,
        )
        project = self.repo.create(project)

        # Tự động thêm người tạo làm PROJECT_MANAGER
        if manager_id is not None:
            self._ensure_project_manager_membership(project.id, manager_id, actor.id)

        # Ghi status history khởi đầu
        self._write_status_history(project.id, None,
                                   project.status, actor.id,
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
            project_weight=project.project_weight or 1,
            department_id=project.department_id,
            manager_id=project.manager_id,
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

        if "name" in data:
            data["name"] = data["name"].strip()
            if not data["name"]:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    "Project name must not be blank")
        if "code" in data:
            data["code"] = data["code"].strip() if data["code"] else None
            if data["code"] and data["code"] != project.code:
                self._ensure_unique_code(data["code"], project_id)
        next_department_id = data.get("department_id", project.department_id)
        self._validate_department(next_department_id)
        if actor.role == UserRole.MANAGER and next_department_id != actor.department_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Manager cannot move projects outside their department")
        next_manager_id = data.get("manager_id", project.manager_id)
        self._validate_project_manager(next_manager_id, next_department_id)
        self._validate_project_dates(
            data.get("start_date", project.start_date),
            data.get("end_date", project.end_date),
        )

        auditable_fields = [
            "name", "code", "description", "priority",
            "start_date", "end_date", "estimated_hours",
            "estimated_budget", "project_weight", "department_id", "manager_id",
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
        if project.manager_id is not None:
            self._ensure_project_manager_membership(project.id, project.manager_id, actor.id)

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
        counts = self.repo.get_task_counts(project_id)
        if counts["total"] > 0:
            old_status = project.status
            if project.status != ProjectStatus.ARCHIVED.value:
                project.status = ProjectStatus.ARCHIVED.value
                project.archived_at = datetime.now(timezone.utc)
                project.updated_by = actor.id
                self._write_status_history(project.id, old_status,
                                           ProjectStatus.ARCHIVED.value, actor.id,
                                           "Archived instead of deleting a project with tasks")
                self._write_audit_log(project.id, actor.id, "status",
                                      old_status, ProjectStatus.ARCHIVED.value)
                self.repo.update(project)
            log_system_activity(
                db=self.db, user_id=actor.id,
                action_type="ARCHIVE", entity_type="PROJECT", entity_id=project_id,
                description=f"Archive project with existing tasks: {project.name}",
            )
            return
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
        self._check_member_manage_access(project, actor)
        self._ensure_project_accepts_member_changes(project, actor)
        target_user = self._get_active_user_or_404(req.user_id)
        self._ensure_actor_can_add_user(project, target_user, actor)
        self._ensure_contribution_total(project_id, req.contribution_share, exclude_user_id=req.user_id)

        existing = self.repo.get_member(project_id, req.user_id)
        if existing and existing.is_active:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                "Người dùng đã là thành viên của project này")

        if existing:
            existing.role = req.role
            existing.contribution_share = req.contribution_share
            existing.is_active = req.is_active
            existing.added_by = actor.id
            member = self.repo.update_member(existing)
        else:
            member = self._add_member_internal(
                project_id, req.user_id, req.role, actor.id,
                req.contribution_share, req.is_active,
            )

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

    def list_members(self, project_id: int, actor: User) -> list[ProjectMemberRead]:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)
        return [ProjectMemberRead.from_member(m) for m in self.repo.list_members(project_id)]

    def list_assignable_users(self, project_id: int, actor: User) -> list[AssignableUserRead]:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)
        return [
            AssignableUserRead(
                id=member.user.id,
                full_name=member.user.full_name,
                email=member.user.email,
                department_id=member.user.department_id,
                project_role=member.role,
            )
            for member in self.repo.list_members(project_id, active_only=True)
            if member.user and member.user.is_active
        ]

    def list_project_tasks(self, project_id: int, actor: User) -> list[TaskSummary]:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)
        tasks = (
            self.db.query(Task)
            .filter(Task.project_id == project_id)
            .order_by(Task.id.desc())
            .limit(500)
            .all()
        )
        return [self._task_to_summary(task) for task in tasks]

    def remove_member(self, project_id: int, user_id: int, actor: User) -> None:
        project = self._get_project_or_404(project_id)
        self._check_member_manage_access(project, actor)
        self._ensure_project_accepts_member_changes(project, actor)

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
        self._check_member_manage_access(project, actor)
        self._ensure_project_accepts_member_changes(project, actor)

        member = self.repo.get_member(project_id, user_id)
        if not member:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                "Không tìm thấy thành viên")

        if req.contribution_share is not None:
            self._ensure_contribution_total(project_id, req.contribution_share, exclude_user_id=user_id)
            self._write_audit_log(project_id, actor.id, "member_contribution_share",
                                  str(member.contribution_share), str(req.contribution_share))
            member.contribution_share = req.contribution_share
        if req.role is not None:
            self._write_audit_log(project_id, actor.id, "member_role",
                                  member.role.value, req.role.value)
            member.role = req.role
        if req.is_active is not None:
            self._write_audit_log(project_id, actor.id, "member_is_active",
                                  str(member.is_active), str(req.is_active))
            member.is_active = req.is_active
        self.repo.update_member(member)
        return ProjectMemberRead.from_member(member)

    # ═══════════════════════════════════════════════════════════════════
    # Milestone Management
    # ═══════════════════════════════════════════════════════════════════

    def create_milestone(self, project_id: int, payload: MilestoneCreate,
                         actor: User) -> MilestoneRead:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)
        self._ensure_project_accepts_content_changes(project)

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

    def update_milestone(self, project_id: int, milestone_id: int,
                         payload: MilestoneUpdate, actor: User) -> MilestoneRead:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)
        self._ensure_project_accepts_content_changes(project)
        milestone = self._get_project_milestone_or_404(project_id, milestone_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(milestone, field, value)
        milestone = self.repo.update_milestone(milestone)
        ProjectProgressEngine(self.db).calculate(project)
        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="UPDATE", entity_type="PROJECT", entity_id=project_id,
            description=f"Update milestone '{milestone.title}'",
        )
        return MilestoneRead.model_validate(milestone)

    def delete_milestone(self, project_id: int, milestone_id: int,
                         actor: User) -> None:
        project = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)
        self._ensure_project_accepts_content_changes(project)
        milestone = self._get_project_milestone_or_404(project_id, milestone_id)
        title = milestone.title
        self.repo.delete_milestone(milestone)
        ProjectProgressEngine(self.db).calculate(project)
        log_system_activity(
            db=self.db, user_id=actor.id,
            action_type="DELETE", entity_type="PROJECT", entity_id=project_id,
            description=f"Delete milestone '{title}'",
        )

    def complete_milestone(self, project_id: int, milestone_id: int,
                           actor: User) -> MilestoneRead:
        project   = self._get_project_or_404(project_id)
        self._check_write_access(project, actor)
        self._ensure_project_accepts_content_changes(project)

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

    def get_report(self, project_id: int, actor: User) -> ProjectReportRead:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)
        counts = self.repo.get_task_counts(project_id)
        analytics = self._build_analytics(project, counts, ProjectProgressEngine(self.db))
        members = self.repo.list_members(project_id, active_only=True)
        performance = [self._to_member_performance(project_id, member) for member in members]
        top_contributor = max(performance, key=lambda item: item.contribution_share, default=None)
        most_overdue = max(performance, key=lambda item: item.overdue_tasks, default=None)
        if most_overdue and most_overdue.overdue_tasks == 0:
            most_overdue = None
        return ProjectReportRead(
            analytics=analytics,
            task_status_breakdown={
                "todo": counts["pending"],
                "doing": counts["doing"],
                "in_review": counts.get("review", 0),
                "blocked": counts["blocked"],
                "done": counts["completed"],
            },
            member_performance=performance,
            top_contributor=top_contributor,
            most_overdue_member=most_overdue,
        )

    def get_dashboard_analytics(self, actor: User) -> dict:
        """Analytics tổng quan toàn bộ project — dùng cho dashboard."""
        if actor.role == UserRole.STAFF:
            projects = self.repo.get_projects_for_member(actor.id)
        elif actor.role == UserRole.MANAGER:
            projects = self.repo.list_for_manager(actor.id, actor.department_id, limit=200)
        else:
            projects = self.repo.list(limit=200)

        status_counts = {}
        for p in projects:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1

        overdue_projects = [
            p for p in projects
            if p.end_date and p.end_date < business_today()
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

    def list_my_projects(self, actor: User) -> list[MyProjectRead]:
        if actor.role == UserRole.ADMIN:
            projects = self.repo.list(limit=500)
        elif actor.role == UserRole.MANAGER:
            projects = self.repo.list_for_manager(actor.id, actor.department_id, limit=500)
        else:
            projects = self.repo.get_projects_for_member(actor.id)
        return [self._to_my_project(p, actor) for p in projects]

    def get_my_project(self, project_id: int, actor: User) -> MyProjectRead:
        project = self._get_project_or_404(project_id)
        self._check_read_access(project, actor)
        return self._to_my_project(project, actor)

    def list_my_tasks(self, actor: User, project_id: int | None = None) -> list[TaskSummary]:
        query = self.db.query(Task).filter(Task.assignee_id == actor.id)
        if project_id is not None:
            project = self._get_project_or_404(project_id)
            self._check_read_access(project, actor)
            query = query.filter(Task.project_id == project_id)
        return [self._task_to_summary(t) for t in query.order_by(Task.id.desc()).limit(200).all()]

    def get_manager_projects(self, actor: User) -> list[ProjectListItem]:
        if actor.role == UserRole.ADMIN:
            return self.list_projects(actor, limit=500)
        if actor.role != UserRole.MANAGER:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Manager or admin role required")
        return self.list_projects(actor, department_id=actor.department_id, limit=500)

    def get_team_workload(self, actor: User) -> list[TeamWorkloadRead]:
        if actor.role not in {UserRole.ADMIN, UserRole.MANAGER}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Manager or admin role required")
        users_query = self.db.query(User).filter(User.is_active == True)
        if actor.role == UserRole.MANAGER:
            users_query = users_query.filter(User.department_id == actor.department_id)
        return [self._to_workload(u) for u in users_query.order_by(User.full_name.asc()).all()]

    def get_user_projects_for_manager(self, user_id: int, actor: User) -> list[MyProjectRead]:
        if actor.role not in {UserRole.ADMIN, UserRole.MANAGER}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Manager or admin role required")
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        if actor.role == UserRole.MANAGER and user.department_id != actor.department_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to view users outside your department")
        return [self._to_my_project(p, user) for p in self.repo.get_projects_for_member(user_id)]

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
        if (not member or not member.is_active) and project.manager_id != actor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Không có quyền xem project này")

    def _check_write_access(self, project: Project, actor: User) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if actor.role == UserRole.MANAGER and project.department_id == actor.department_id:
            return
        # Project Manager trong project
        member = self.repo.get_member(project.id, actor.id)
        if member and member.is_active and member.role in {ProjectMemberRole.PROJECT_MANAGER, ProjectMemberRole.TEAM_LEAD}:
            return
        if project.manager_id == actor.id:
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Không có quyền chỉnh sửa project này")

    def _check_member_manage_access(self, project: Project, actor: User) -> None:
        self._check_write_access(project, actor)

    def _ensure_project_accepts_member_changes(self, project: Project, actor: User) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if project.status in {
            ProjectStatus.COMPLETED.value,
            ProjectStatus.CANCELLED.value,
            ProjectStatus.ARCHIVED.value,
        }:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cannot change members of terminal projects")

    def _ensure_project_accepts_content_changes(self, project: Project) -> None:
        if project.status in {
            ProjectStatus.COMPLETED.value,
            ProjectStatus.CANCELLED.value,
            ProjectStatus.ARCHIVED.value,
        }:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cannot change content of terminal projects")

    def _get_active_user_or_404(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        if not user.is_active:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "User must be active")
        return user

    def _ensure_actor_can_add_user(self, project: Project, target_user: User, actor: User) -> None:
        if actor.role == UserRole.ADMIN:
            return
        if project.department_id and target_user.department_id != project.department_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User must belong to the project department")
        if actor.role == UserRole.MANAGER and target_user.department_id != actor.department_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Manager cannot add users outside their department")

    def _ensure_contribution_total(self, project_id: int, new_share: float, exclude_user_id: int | None = None) -> None:
        query = self.db.query(func.coalesce(func.sum(ProjectMember.contribution_share), 0)).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True,
        )
        if exclude_user_id is not None:
            query = query.filter(ProjectMember.user_id != exclude_user_id)
        current_total = float(query.scalar() or 0)
        if current_total + float(new_share or 0) > 100:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Active member contribution_share cannot exceed 100%")

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

    def _ensure_unique_code(self, code: str | None, current_project_id: int | None = None) -> None:
        if not code:
            return
        query = self.db.query(Project).filter(Project.code == code)
        if current_project_id is not None:
            query = query.filter(Project.id != current_project_id)
        if query.first():
            raise HTTPException(status.HTTP_409_CONFLICT, "Project code already exists")

    def _validate_department(self, department_id: int | None) -> None:
        if department_id is None or self.db.get(Department, department_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")

    def _validate_project_dates(self, start_date, end_date) -> None:
        if start_date and end_date and end_date < start_date:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Project end_date must not be before start_date",
            )

    def _validate_project_manager(self, manager_id: int | None,
                                  department_id: int | None = None) -> None:
        if manager_id is None:
            return
        manager = self.db.get(User, manager_id)
        if manager is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project manager not found")
        if not manager.is_active:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Project manager must be active")
        if manager.role not in {UserRole.ADMIN, UserRole.MANAGER}:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Project manager must have admin or manager role")
        if manager.role == UserRole.MANAGER and department_id is not None and manager.department_id != department_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Project manager must belong to the project department")

    def _ensure_project_manager_membership(self, project_id: int, manager_id: int,
                                           added_by: int) -> ProjectMember:
        member = self.repo.get_member(project_id, manager_id)
        if member:
            member.role = ProjectMemberRole.PROJECT_MANAGER
            member.is_active = True
            member.added_by = added_by
            return self.repo.update_member(member)
        return self._add_member_internal(
            project_id, manager_id, ProjectMemberRole.PROJECT_MANAGER, added_by
        )

    def _get_project_milestone_or_404(self, project_id: int,
                                      milestone_id: int) -> ProjectMilestone:
        milestone = self.repo.get_milestone(milestone_id)
        if not milestone or milestone.project_id != project_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
        return milestone

    def _add_member_internal(self, project_id: int, user_id: int,
                              role: ProjectMemberRole, added_by: int,
                              contribution_share: float = 0,
                              is_active: bool = True,
                              ) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id, user_id=user_id,
            role=role, added_by=added_by,
            contribution_share=contribution_share,
            is_active=is_active,
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
            ProjectMember.project_id == project.id,
            ProjectMember.is_active == True,
        ).count()
        is_overdue = bool(
            project.end_date and project.end_date < business_today()
            and project.status not in ("COMPLETED", "CANCELLED", "ARCHIVED")
        )
        return ProjectListItem(
            id=project.id, name=project.name, description=project.description,
            code=project.code,
            status=project.status,
            priority=project.priority.value if project.priority else "MEDIUM",
            progress_percentage=project.progress_percentage or 0,
            start_date=project.start_date, end_date=project.end_date,
            estimated_hours=project.estimated_hours,
            estimated_budget=project.estimated_budget,
            department_id=project.department_id, manager_id=project.manager_id,
            department_name=project.department.name if project.department else "",
            manager_name=project.manager.full_name if project.manager else "",
            total_tasks=counts["total"],
            completed_tasks=counts["completed"],
            done_tasks=counts["completed"],
            task_completion_percentage=round(
                counts["completed"] / counts["total"] * 100, 1
            ) if counts["total"] else 0,
            project_progress_percentage=project.progress_percentage or 0,
            overdue_tasks=counts["overdue"],
            member_count=member_count,
            total_members=member_count,
            milestone_count=len(milestones),
            milestones_done=sum(1 for m in milestones if m.is_completed),
            is_overdue=is_overdue,
            project_weight=project.project_weight or 1,
        )

    def _to_my_project(self, project: Project, actor: User) -> MyProjectRead:
        member = self.repo.get_member(project.id, actor.id)
        stats = self._task_stats_for_user(project.id, actor.id)
        health = self._project_health(project, stats["overdue_tasks"])
        return MyProjectRead(
            project_id=project.id,
            project_code=project.code,
            project_name=project.name,
            description=project.description,
            department=project.department.name if project.department else "",
            project_status=project.status,
            project_role=member.role if member and member.is_active else None,
            contribution_share=member.contribution_share if member and member.is_active else 0,
            start_date=project.start_date,
            due_date=project.end_date,
            progress=project.progress_percentage or 0,
            project_health=health,
            **stats,
        )

    def _task_stats_for_user(self, project_id: int, user_id: int) -> dict[str, int]:
        rows = (
            self.db.query(Task.status, func.count(Task.id))
            .filter(Task.project_id == project_id, Task.assignee_id == user_id)
            .group_by(Task.status)
            .all()
        )
        counts = {
            (status_value.value if hasattr(status_value, "value") else status_value): count
            for status_value, count in rows
        }
        overdue = (
            self.db.query(func.count(Task.id))
            .filter(
                Task.project_id == project_id,
                Task.assignee_id == user_id,
                Task.status != TaskStatus.DONE,
                Task.deadline.isnot(None),
                Task.deadline < business_today(),
            )
            .scalar() or 0
        )
        return {
            "assigned_tasks": sum(counts.values()),
            "doing_tasks": counts.get(TaskStatus.DOING.value, 0),
            "review_tasks": counts.get(TaskStatus.IN_REVIEW.value, 0),
            "done_tasks": counts.get(TaskStatus.DONE.value, 0),
            "overdue_tasks": overdue,
        }

    def _to_member_performance(self, project_id: int,
                               member: ProjectMember) -> ProjectMemberPerformanceRead:
        from app.models.kpi_snapshot import KpiSnapshot

        stats = self._task_stats_for_user(project_id, member.user_id)
        total_tasks = stats["assigned_tasks"]
        done_tasks = stats["done_tasks"]
        snapshot = (
            self.db.query(KpiSnapshot)
            .filter(KpiSnapshot.user_id == member.user_id)
            .order_by(KpiSnapshot.period_key.desc())
            .first()
        )
        return ProjectMemberPerformanceRead(
            user_id=member.user_id,
            full_name=member.user.full_name if member.user else "",
            email=member.user.email if member.user else "",
            department_name=member.user.department.name if member.user and member.user.department else "",
            project_role=member.role,
            contribution_share=member.contribution_share or 0,
            total_tasks=total_tasks,
            done_tasks=done_tasks,
            overdue_tasks=stats["overdue_tasks"],
            task_completion_percentage=round(done_tasks / total_tasks * 100, 1) if total_tasks else 0,
            kpi_score=float(snapshot.total_score or 0) if snapshot else 0,
        )

    def _project_health(self, project: Project, user_overdue: int = 0) -> str:
        if project.status == ProjectStatus.COMPLETED.value:
            return "COMPLETED"
        if user_overdue > 0 or (project.end_date and project.end_date < business_today() and project.status not in {"COMPLETED", "CANCELLED", "ARCHIVED"}):
            return "OVERDUE"
        if project.end_date and (project.end_date - business_today()).days <= 7 and (project.progress_percentage or 0) < 80:
            return "AT_RISK"
        return "OK"

    def _to_workload(self, user: User) -> TeamWorkloadRead:
        active_projects = (
            self.db.query(func.count(ProjectMember.id))
            .filter(ProjectMember.user_id == user.id, ProjectMember.is_active == True)
            .scalar() or 0
        )
        tasks = self.db.query(Task).filter(Task.assignee_id == user.id, Task.status != TaskStatus.DONE).all()
        estimated = sum(float(t.estimated_hours or t.base_weight or 0) for t in tasks)
        actual = sum(float(t.actual_hours or 0) for t in tasks)
        overdue = sum(1 for t in tasks if t.deadline and t.deadline < business_today())
        workload_status = "OVERLOADED" if estimated >= 40 or len(tasks) >= 10 else "UNDER_ASSIGNED" if active_projects == 0 else "NORMAL"
        return TeamWorkloadRead(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            active_projects=active_projects,
            assigned_tasks=len(tasks),
            doing_tasks=sum(1 for t in tasks if t.status == TaskStatus.DOING),
            review_tasks=sum(1 for t in tasks if t.status == TaskStatus.IN_REVIEW),
            overdue_tasks=overdue,
            estimated_hours=round(estimated, 2),
            actual_hours=round(actual, 2),
            workload_status=workload_status,
        )

    def _build_analytics(self, project: Project, counts: dict,
                          engine: ProjectProgressEngine) -> ProjectAnalytics:
        today       = business_today()
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
            if t.done_at and t.deadline and completion_business_date(t.done_at) <= t.deadline
        )
        on_time_rate = (on_time_count / completed * 100) if completed else 0
        project_tasks = self.db.query(Task).filter(Task.project_id == project.id).all()
        estimated_hours = sum(float(task.estimated_hours or 0) for task in project_tasks)
        actual_hours = sum(float(task.actual_hours or 0) for task in project_tasks)

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
        if (project.progress_percentage or 0) < 30 and project.end_date:
            remaining = (project.end_date - today).days
            if remaining < 14:
                risk_indicators.append("Tiến độ thấp, deadline gần")

        n = len(risk_indicators)
        risk_level = "LOW" if n == 0 else "MEDIUM" if n == 1 else "HIGH" if n == 2 else "CRITICAL"

        return ProjectAnalytics(
            progress_percentage=project.progress_percentage or 0,
            project_progress_percentage=project.progress_percentage or 0,
            total_tasks=total, completed_tasks=completed,
            done_tasks=completed,
            pending_tasks=counts["pending"], todo_tasks=counts["pending"],
            doing_tasks=counts["doing"],
            review_tasks=counts.get("review", 0),
            blocked_tasks=counts["blocked"], overdue_tasks=counts["overdue"],
            completion_rate=round(completed / total * 100, 1) if total else 0,
            task_completion_percentage=round(completed / total * 100, 1) if total else 0,
            on_time_rate=round(on_time_rate, 1),
            velocity=round(velocity, 2),
            estimated_hours=round(estimated_hours, 2),
            actual_hours=round(actual_hours, 2),
            # No actual-cost field exists yet, so a real budget ratio cannot be calculated.
            budget_utilization=None,
            milestone_progress=round(ms_pct, 1),
            total_members=self.db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id,
                ProjectMember.is_active == True,
            ).count(),
            total_milestones=ms_total,
            completed_milestones=ms_done,
            milestone_completion_percentage=round(ms_pct, 1),
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
            if t.status != TaskStatus.DONE and t.deadline and t.deadline < business_today()
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
        today = business_today()
        from app.utils.task_ultis import infer_priority
        return TaskSummary(
            id=task.id, title=task.title, status=task.status,
            priority=infer_priority(task.base_weight),
            deadline=task.deadline,
            done_at=task.done_at,
            base_weight=task.base_weight or 1,
            assignee_id=task.assignee_id,
            assignee_name=task.assignee.full_name if task.assignee else "",
            project_id=task.project_id,
            department_id=task.department_id,
            is_overdue=bool(
                task.status != "done" and task.deadline and task.deadline < today
            ),
        )

    @staticmethod
    def _generate_code(name: str) -> str:
        import re, time
        prefix = re.sub(r"[^A-Za-z0-9]", "", name[:6]).upper() or "PRJ"
        return f"{prefix}-{int(time.time()) % 100000}"
