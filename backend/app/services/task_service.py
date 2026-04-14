from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session) -> None:
        self.repository = TaskRepository(db)

    def create_task(self, payload: TaskCreate) -> Task:
        task = Task(**payload.model_dump())
        if task.status == TaskStatus.DONE and task.done_at is None:
            task.done_at = datetime.utcnow()
        return self.repository.create(task)

    def list_tasks(self, status: TaskStatus | None = None, overdue: bool | None = None) -> list[Task]:
        return self.repository.list(status=status, overdue=overdue)

    def get_task(self, task_id: int) -> Task:
        task = self.repository.get_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    def update_task(self, task_id: int, payload: TaskUpdate) -> Task:
        task = self.get_task(task_id)
        data = payload.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(task, field, value)

        if payload.status == TaskStatus.DONE and task.done_at is None:
            task.done_at = datetime.utcnow()
        elif payload.status in {TaskStatus.TODO, TaskStatus.DOING}:
            task.done_at = None

        return self.repository.update(task)

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        self.repository.delete(task)
