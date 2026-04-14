from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, task: Task) -> Task:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        return self.db.get(Task, task_id)

    def list(self, status: TaskStatus | None = None, overdue: bool | None = None) -> list[Task]:
        stmt: Select[tuple[Task]] = select(Task).order_by(Task.id.desc())

        if status is not None:
            stmt = stmt.where(Task.status == status)

        if overdue is True:
            stmt = stmt.where(Task.deadline.is_not(None), Task.deadline < date.today(), Task.status != TaskStatus.DONE)

        return list(self.db.scalars(stmt).all())

    def update(self, task: Task) -> Task:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.commit()
