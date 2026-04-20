from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_authenticated_user
from app.db.session import get_db
from app.models.task import TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> TaskRead:
    service = TaskService(db)
    return service.create_task(current_user, payload)


@router.get("", response_model=list[TaskRead])
def list_tasks(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    status: TaskStatus | None = Query(default=None),
    overdue: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    service = TaskService(db)
    return service.list_tasks(current_user, status=status, overdue=overdue)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> TaskRead:
    service = TaskService(db)
    return service.get_task_for_actor(current_user, task_id)


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> TaskRead:
    service = TaskService(db)
    return service.update_task(current_user, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> Response:
    service = TaskService(db)
    service.delete_task(current_user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
