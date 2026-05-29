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
    reason: str | None        = None   # lý do đổi status (ghi vào history)


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    full_name: str = ""
    email: str     = ""
    role: ProjectMemberRole
    joined_at: datetime

    @classmethod
    def from_member(cls, m: Any) -> "ProjectMemberRead":
        return cls(
            id=m.id, user_id=m.user_id,
            full_name=m.user.full_name if m.user else "",
            email=m.user.email if m.user else "",
            role=m.role, joined_at=m.joined_at,
        )


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
    code: str | None
    status: str
    priority: str
    progress_percentage: float
    start_date: date | None
    end_date: date | None
    department_name: str = ""
    manager_name: str    = ""
    total_tasks: int     = 0
    completed_tasks: int = 0
    overdue_tasks: int   = 0
    member_count: int    = 0
    milestone_count: int = 0
    milestones_done: int = 0
    is_overdue: bool     = False


class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: str
    priority: str
    deadline: date | None
    assignee_name: str = ""
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
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    doing_tasks: int
    blocked_tasks: int
    overdue_tasks: int
    completion_rate: float
    on_time_rate: float
    velocity: float               # tasks/tuần trung bình
    estimated_hours: float | None
    actual_hours: float
    budget_utilization: float | None
    milestone_progress: float     # % milestones hoàn thành
    risk_level: str               # LOW / MEDIUM / HIGH / CRITICAL
    risk_indicators: list[str]


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


class UpdateMemberRoleRequest(BaseModel):
    role: ProjectMemberRole