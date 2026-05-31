"""Schemas Pydantic cho Enterprise Project Management."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectMemberRole, ProjectPriority, ProjectStatus


# ═══════════════════════════════════════════════════════════════════════════
# Project CRUD
# ═══════════════════════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    name: str             = Field(..., min_length=1, max_length=255)
    code: str | None      = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: ProjectPriority = ProjectPriority.MEDIUM
    department_id: int | None = None
    manager_id: int | None    = None
    start_date: date | None   = None
    end_date: date | None     = None
    estimated_hours: float | None  = None
    estimated_budget: float | None = None
    project_weight: float = Field(default=1.0, ge=0.1, le=10)


class ProjectUpdate(BaseModel):
    name: str | None          = Field(default=None, min_length=1, max_length=255)
    code: str | None          = Field(default=None, max_length=50)
    description: str | None   = Field(default=None, max_length=1000)
    status: ProjectStatus | None    = None
    priority: ProjectPriority | None = None
    department_id: int | None = None
    manager_id: int | None    = None
    start_date: date | None   = None
    end_date: date | None     = None
    estimated_hours: float | None  = None
    estimated_budget: float | None = None
    project_weight: float | None = Field(default=None, ge=0.1, le=10)
    reason: str | None        = None   # lý do đổi status (ghi vào history)


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    full_name: str = ""
    email: str     = ""
    role: ProjectMemberRole
    contribution_share: float = 0
    is_active: bool = True
    joined_at: datetime

    @classmethod
    def from_member(cls, m: Any) -> "ProjectMemberRead":
        return cls(
            id=m.id, user_id=m.user_id,
            full_name=m.user.full_name if m.user else "",
            email=m.user.email if m.user else "",
            role=m.role,
            contribution_share=m.contribution_share or 0,
            is_active=bool(m.is_active),
            joined_at=m.joined_at,
        )


class AssignableUserRead(BaseModel):
    id: int
    full_name: str
    email: str
    department_id: int
    project_role: ProjectMemberRole


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    due_date: date | None
    is_completed: bool
    completed_at: datetime | None
    weight: int


class MilestoneCreate(BaseModel):
    title: str        = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    due_date: date | None   = None
    weight: int             = Field(default=1, ge=1, le=10)


class MilestoneUpdate(BaseModel):
    title: str | None       = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    due_date: date | None   = None
    weight: int | None      = Field(default=None, ge=1, le=10)


class StatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    from_status: str | None
    to_status: str
    actor_name: str = ""
    reason: str | None
    changed_at: datetime

    @classmethod
    def from_history(cls, h: Any) -> "StatusHistoryRead":
        return cls(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            actor_name=h.actor.full_name if h.actor else "System",
            reason=h.reason,
            changed_at=h.changed_at,
        )


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    field_name: str
    old_value: str | None
    new_value: str | None
    actor_name: str = ""
    changed_at: datetime

    @classmethod
    def from_audit(cls, a: Any) -> "AuditLogRead":
        return cls(
            id=a.id, field_name=a.field_name,
            old_value=a.old_value, new_value=a.new_value,
            actor_name=a.actor.full_name if a.actor else "System",
            changed_at=a.changed_at,
        )


# ── Response tổng hợp ──────────────────────────────────────────────────────

class ProjectListItem(BaseModel):
    """Response nhẹ cho danh sách project."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    code: str | None
    status: str
    priority: str
    progress_percentage: float
    start_date: date | None
    end_date: date | None
    estimated_hours: float | None = None
    estimated_budget: float | None = None
    department_id: int | None = None
    manager_id: int | None    = None
    department_name: str = ""
    manager_name: str    = ""
    total_tasks: int     = 0
    completed_tasks: int = 0
    done_tasks: int      = 0
    task_completion_percentage: float = 0
    project_progress_percentage: float = 0
    overdue_tasks: int   = 0
    member_count: int    = 0
    total_members: int   = 0
    milestone_count: int = 0
    milestones_done: int = 0
    is_overdue: bool     = False
    project_weight: float = 1


class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: str
    priority: str
    deadline: date | None
    done_at: datetime | None = None
    base_weight: int = 1
    assignee_id: int | None = None
    assignee_name: str = ""
    project_id: int | None = None
    department_id: int | None = None
    is_overdue: bool   = False


class ProjectKpiContribution(BaseModel):
    """KPI breakdown cho project."""
    total_score_contributed: float = 0
    tasks_completed: int           = 0
    tasks_overdue: int             = 0
    milestones_completed: int      = 0
    on_time_rate: float            = 0
    member_contributions: list[dict] = []


class ProjectAnalytics(BaseModel):
    """Analytics đầy đủ cho 1 project."""
    progress_percentage: float
    project_progress_percentage: float = 0
    total_tasks: int
    completed_tasks: int
    done_tasks: int = 0
    pending_tasks: int
    todo_tasks: int = 0
    doing_tasks: int
    review_tasks: int = 0
    blocked_tasks: int
    overdue_tasks: int
    completion_rate: float
    task_completion_percentage: float = 0
    on_time_rate: float
    velocity: float               # tasks/tuần trung bình
    estimated_hours: float | None
    actual_hours: float
    budget_utilization: float | None
    milestone_progress: float     # % milestones hoàn thành
    total_members: int = 0
    total_milestones: int = 0
    completed_milestones: int = 0
    milestone_completion_percentage: float = 0
    risk_level: str               # LOW / MEDIUM / HIGH / CRITICAL
    risk_indicators: list[str]


class ProjectMemberPerformanceRead(BaseModel):
    user_id: int
    full_name: str
    email: str
    department_name: str = ""
    project_role: ProjectMemberRole
    contribution_share: float = 0
    total_tasks: int = 0
    done_tasks: int = 0
    overdue_tasks: int = 0
    task_completion_percentage: float = 0
    kpi_score: float = 0


class ProjectReportRead(BaseModel):
    analytics: ProjectAnalytics
    task_status_breakdown: dict[str, int]
    member_performance: list[ProjectMemberPerformanceRead] = []
    top_contributor: ProjectMemberPerformanceRead | None = None
    most_overdue_member: ProjectMemberPerformanceRead | None = None


class ProjectOverview(BaseModel):
    """Response đầy đủ cho Project Detail page."""
    # Thông tin cơ bản
    id: int
    name: str
    code: str | None
    description: str | None
    status: str
    priority: str
    progress_percentage: float
    start_date: date | None
    end_date: date | None
    estimated_hours: float | None
    actual_hours: float
    estimated_budget: float | None
    project_weight: float = 1
    department_id: int | None = None
    manager_id: int | None = None
    department_name: str = ""
    manager_name: str    = ""
    created_at: datetime | None
    updated_at: datetime | None

    # Liên quan
    members: list[ProjectMemberRead]        = []
    milestones: list[MilestoneRead]         = []
    recent_tasks: list[TaskSummary]         = []
    status_history: list[StatusHistoryRead] = []
    recent_audit_logs: list[AuditLogRead]   = []
    analytics: ProjectAnalytics | None      = None
    kpi_contribution: ProjectKpiContribution | None = None


# ── Member management ──────────────────────────────────────────────────────

class AddMemberRequest(BaseModel):
    user_id: int
    role: ProjectMemberRole = ProjectMemberRole.MEMBER
    contribution_share: float = Field(default=0, ge=0, le=100)
    is_active: bool = True


class UpdateMemberRoleRequest(BaseModel):
    role: ProjectMemberRole | None = None
    contribution_share: float | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class MyProjectRead(BaseModel):
    project_id: int
    project_code: str | None
    project_name: str
    description: str | None = None
    department: str = ""
    project_status: str
    project_role: ProjectMemberRole | None = None
    contribution_share: float = 0
    start_date: date | None = None
    due_date: date | None = None
    progress: float = 0
    project_health: str = "OK"
    assigned_tasks: int = 0
    doing_tasks: int = 0
    review_tasks: int = 0
    done_tasks: int = 0
    overdue_tasks: int = 0


class TeamWorkloadRead(BaseModel):
    user_id: int
    full_name: str
    email: str
    active_projects: int = 0
    assigned_tasks: int = 0
    doing_tasks: int = 0
    review_tasks: int = 0
    overdue_tasks: int = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    workload_status: str = "NORMAL"
