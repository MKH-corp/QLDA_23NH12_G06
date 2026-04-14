from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.task import TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    service = TaskService(db)
    return service.create_task(payload)


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status: TaskStatus | None = Query(default=None),
    overdue: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    service = TaskService(db)
    return service.list_tasks(status=status, overdue=overdue)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    service = TaskService(db)
    return service.get_task(task_id)


@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskRead:
    service = TaskService(db)
    return service.update_task(task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    service = TaskService(db)
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
