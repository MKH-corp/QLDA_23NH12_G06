"""
Model Project mở rộng — enterprise-grade.

Giữ backward-compatible với schema cũ (không xóa cột nào).
Thêm: code, manager_id, priority, progress_percentage,
      estimated/actual_hours, budget, created_by, updated_by,
      archived_at, timestamps + relationships.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, Float,
    ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ON_HOLD = "ON_HOLD"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class ProjectPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProjectMemberRole(str, enum.Enum):
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TEAM_LEAD = "TEAM_LEAD"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


# ── Transition rules ────────────────────────────────────────────────────────
# Chỉ các transition này mới được phép — validate ở service layer
ALLOWED_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.PLANNING:  {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
    ProjectStatus.ACTIVE:    {ProjectStatus.PAUSED, ProjectStatus.ON_HOLD, ProjectStatus.REVIEW,
                              ProjectStatus.COMPLETED, ProjectStatus.CANCELLED},
    ProjectStatus.PAUSED:    {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
    ProjectStatus.ON_HOLD:   {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
    ProjectStatus.REVIEW:    {ProjectStatus.ACTIVE, ProjectStatus.COMPLETED,
                              ProjectStatus.CANCELLED},
    ProjectStatus.COMPLETED: {ProjectStatus.ARCHIVED},
    ProjectStatus.CANCELLED: {ProjectStatus.ARCHIVED},
    ProjectStatus.ARCHIVED:  set(),   # terminal state
}


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("code", name="uq_projects_code"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # ── Định danh ──────────────────────────────────────────────────────
    name        = Column(String(255), nullable=False)
    code        = Column(String(50),  nullable=True)   # VD: PRJ-2026-001
    description = Column(String(1000), nullable=True)

    # ── Trạng thái & ưu tiên ──────────────────────────────────────────
    # Giữ kiểu String để backward-compatible; validate bằng Enum ở service
    status      = Column(String(50), nullable=False, server_default="PLANNING")
    priority    = Column(
        Enum(ProjectPriority, name="project_priority", create_constraint=False),
        nullable=False, server_default="MEDIUM"
    )

    # ── Tiến độ (tính bởi ProgressEngine, không hardcode) ─────────────
    progress_percentage = Column(Float, nullable=False, server_default="0")

    # ── Thời gian ─────────────────────────────────────────────────────
    start_date = Column(Date, nullable=True)
    end_date   = Column(Date, nullable=True)

    # ── Ước tính & thực tế ────────────────────────────────────────────
    estimated_hours  = Column(Float, nullable=True)
    actual_hours     = Column(Float, nullable=False, server_default="0")
    estimated_budget = Column(Float, nullable=True)
    project_weight   = Column(Float, nullable=False, server_default="1")

    # ── Liên kết tổ chức ──────────────────────────────────────────────
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id    = Column(Integer, ForeignKey("users.id",    ondelete="SET NULL"), nullable=True)

    # ── Audit timestamps ──────────────────────────────────────────────
    created_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(),
                         onupdate=func.now(), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────
    department  = relationship("Department", foreign_keys=[department_id])
    manager     = relationship("User", foreign_keys=[manager_id])
    creator     = relationship("User", foreign_keys=[created_by])
    tasks       = relationship("Task", back_populates="project")
    members     = relationship("ProjectMember", back_populates="project",
                               cascade="all, delete-orphan")
    milestones  = relationship("ProjectMilestone", back_populates="project",
                               cascade="all, delete-orphan",
                               order_by="ProjectMilestone.due_date")
    status_history = relationship("ProjectStatusHistory", back_populates="project",
                                  cascade="all, delete-orphan",
                                  order_by="ProjectStatusHistory.changed_at.desc()")
    audit_logs  = relationship("ProjectAuditLog", back_populates="project",
                               cascade="all, delete-orphan",
                               order_by="ProjectAuditLog.changed_at.desc()")


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    id         = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id",  ondelete="CASCADE"), nullable=False, index=True)
    user_id    = Column(Integer, ForeignKey("users.id",     ondelete="CASCADE"), nullable=False, index=True)
    role       = Column(
        Enum(ProjectMemberRole, name="project_member_role", create_constraint=False),
        nullable=False, server_default="MEMBER"
    )
    joined_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    added_by   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    contribution_share = Column(Float, nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default="true")

    project    = relationship("Project",  back_populates="members")
    user       = relationship("User",     foreign_keys=[user_id],  lazy="joined")
    added_by_user = relationship("User",  foreign_keys=[added_by])


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id           = Column(Integer, primary_key=True)
    project_id   = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title        = Column(String(255), nullable=False)
    description  = Column(String(1000), nullable=True)
    due_date     = Column(Date, nullable=True)
    is_completed = Column(Boolean, nullable=False, server_default="false")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    weight       = Column(Integer, nullable=False, server_default="1")
    created_by   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project      = relationship("Project", back_populates="milestones")
    creator      = relationship("User", foreign_keys=[created_by])


class ProjectStatusHistory(Base):
    __tablename__ = "project_status_history"

    id          = Column(Integer, primary_key=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status   = Column(String(50), nullable=False)
    changed_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason      = Column(String(500), nullable=True)
    changed_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project     = relationship("Project", back_populates="status_history")
    actor       = relationship("User", foreign_keys=[changed_by], lazy="joined")


class ProjectAuditLog(Base):
    __tablename__ = "project_audit_logs"

    id          = Column(Integer, primary_key=True)
    project_id  = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    field_name  = Column(String(100), nullable=False)
    old_value   = Column(Text, nullable=True)
    new_value   = Column(Text, nullable=True)
    changed_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project     = relationship("Project", back_populates="audit_logs")
    actor       = relationship("User", foreign_keys=[changed_by], lazy="joined")
