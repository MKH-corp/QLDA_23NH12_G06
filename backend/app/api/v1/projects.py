"""
Project API Router — router chỉ lo HTTP, toàn bộ logic ở ProjectService.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.models.user import User
from app.schemas.project import (
    AddMemberRequest, MilestoneCreate, MilestoneRead,
    ProjectCreate, ProjectKpiContribution, ProjectListItem,
    ProjectMemberRead, ProjectOverview, ProjectUpdate,
    UpdateMemberRoleRequest, ProjectAnalytics,
)
from app.services.project_service import ProjectService

router = APIRouter()

CurrentUser = Annotated[User, Depends(require_authenticated_user)]
DB = Annotated[Session, Depends(get_db)]


# ═══════════════════════════════════════════════════════════════════════════
# Projects CRUD
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=list[ProjectListItem])
def list_projects(
    current_user: CurrentUser, db: DB,
    department_id: int | None = Query(default=None),
    status: str | None       = Query(default=None),
    skip: int                = Query(default=0, ge=0),
    limit: int               = Query(default=50, ge=1, le=200),
):
    return ProjectService(db).list_projects(current_user, department_id, status, skip, limit)


@router.post("/", response_model=ProjectListItem, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, current_user: CurrentUser, db: DB,
):
    return ProjectService(db).create_project(payload, current_user)


@router.get("/dashboard", response_model=dict)
def get_dashboard_analytics(current_user: CurrentUser, db: DB):
    return ProjectService(db).get_dashboard_analytics(current_user)


@router.get("/{project_id}", response_model=ProjectOverview)
def get_project_overview(project_id: int, current_user: CurrentUser, db: DB):
    return ProjectService(db).get_project_overview(project_id, current_user)


@router.put("/{project_id}", response_model=ProjectListItem)
def update_project(
    project_id: int, payload: ProjectUpdate,
    current_user: CurrentUser, db: DB,
):
    return ProjectService(db).update_project(project_id, payload, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, current_user: CurrentUser, db: DB):
    ProjectService(db).delete_project(project_id, current_user)


# ═══════════════════════════════════════════════════════════════════════════
# Members
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/{project_id}/members", response_model=ProjectMemberRead,
             status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: int, req: AddMemberRequest,
    current_user: CurrentUser, db: DB,
):
    return ProjectService(db).add_member(project_id, req, current_user)


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMemberRead)
def update_member_role(
    project_id: int, user_id: int,
    req: UpdateMemberRoleRequest,
    current_user: CurrentUser, db: DB,
):
    return ProjectService(db).update_member_role(project_id, user_id, req, current_user)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    project_id: int, user_id: int,
    current_user: CurrentUser, db: DB,
):
    ProjectService(db).remove_member(project_id, user_id, current_user)


# ═══════════════════════════════════════════════════════════════════════════
# Milestones
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/{project_id}/milestones", response_model=MilestoneRead,
             status_code=status.HTTP_201_CREATED)
def create_milestone(
    project_id: int, payload: MilestoneCreate,
    current_user: CurrentUser, db: DB,
):
    return ProjectService(db).create_milestone(project_id, payload, current_user)


@router.patch("/{project_id}/milestones/{milestone_id}/complete",
              response_model=MilestoneRead)
def complete_milestone(
    project_id: int, milestone_id: int,
    current_user: CurrentUser, db: DB,
):
    return ProjectService(db).complete_milestone(project_id, milestone_id, current_user)


# ═══════════════════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/{project_id}/analytics", response_model=ProjectAnalytics)
def get_project_analytics(project_id: int, current_user: CurrentUser, db: DB):
    return ProjectService(db).get_analytics(project_id, current_user)


@router.get("/{project_id}/kpi", response_model=ProjectKpiContribution)
def get_project_kpi(project_id: int, current_user: CurrentUser, db: DB):
    svc = ProjectService(db)
    project = svc._get_project_or_404(project_id)
    svc._check_read_access(project, current_user)
    return svc._build_kpi_contribution(project_id)