from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.models.user import User
from app.schemas.project import MyProjectRead, TaskSummary
from app.services.project_service import ProjectService

router = APIRouter(prefix="/me", tags=["me"])

CurrentUser = Annotated[User, Depends(require_authenticated_user)]
DB = Annotated[Session, Depends(get_db)]


@router.get("/projects", response_model=list[MyProjectRead])
def list_my_projects(current_user: CurrentUser, db: DB):
    return ProjectService(db).list_my_projects(current_user)


@router.get("/projects/{project_id}", response_model=MyProjectRead)
def get_my_project(project_id: int, current_user: CurrentUser, db: DB):
    return ProjectService(db).get_my_project(project_id, current_user)


@router.get("/tasks", response_model=list[TaskSummary])
def list_my_tasks(
    current_user: CurrentUser,
    db: DB,
    project_id: int | None = Query(default=None),
):
    return ProjectService(db).list_my_tasks(current_user, project_id)
