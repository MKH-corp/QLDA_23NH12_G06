from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.models.user import User
from app.schemas.project import MyProjectRead, ProjectListItem, ProjectMemberRead, TeamWorkloadRead
from app.services.project_service import ProjectService

router = APIRouter(prefix="/manager", tags=["manager"])

CurrentUser = Annotated[User, Depends(require_authenticated_user)]
DB = Annotated[Session, Depends(get_db)]


@router.get("/projects", response_model=list[ProjectListItem])
def list_manager_projects(current_user: CurrentUser, db: DB):
    return ProjectService(db).get_manager_projects(current_user)


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberRead])
def list_manager_project_members(project_id: int, current_user: CurrentUser, db: DB):
    return ProjectService(db).list_members(project_id, current_user)


@router.get("/team-workload", response_model=list[TeamWorkloadRead])
def get_team_workload(current_user: CurrentUser, db: DB):
    return ProjectService(db).get_team_workload(current_user)


@router.get("/users/{user_id}/projects", response_model=list[MyProjectRead])
def get_user_projects(user_id: int, current_user: CurrentUser, db: DB):
    return ProjectService(db).get_user_projects_for_manager(user_id, current_user)
