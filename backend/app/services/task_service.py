from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.department_service import DepartmentService


class TaskService:
    def __init__(self, db: Session) -> None:
        self.repository = TaskRepository(db)
        self.user_repository = UserRepository(db)
        self.department_service = DepartmentService(db)

    def create_task(self, actor: User, payload: TaskCreate) -> Task:
        if actor.role == UserRole.STAFF:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff cannot create tasks")

        assignee = self._get_user_or_404(payload.assignee_id)
        department = self.department_service.ensure_department_exists(payload.department_id)
        self._ensure_assignee_matches_department(assignee, department.id)

        if actor.role == UserRole.MANAGER and department.id != actor.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create tasks outside your department")

        task = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status,
            deadline=payload.deadline,
            base_weight=payload.base_weight,
            creator_id=actor.id,
            assignee_id=payload.assignee_id,
            department_id=payload.department_id,
        )
        if task.status == TaskStatus.DONE and task.done_at is None:
            task.done_at = datetime.now(UTC).replace(tzinfo=None)
        return self.repository.create(task)

    def list_tasks(self, actor: User, status: TaskStatus | None = None, overdue: bool | None = None) -> list[Task]:
        if actor.role == UserRole.ADMIN:
            return self.repository.list(status=status, overdue=overdue)
        if actor.role == UserRole.MANAGER:
            return self.repository.list(status=status, overdue=overdue, department_id=actor.department_id)
        return self.repository.list(status=status, overdue=overdue, assignee_id=actor.id)

    def get_task_for_actor(self, actor: User, task_id: int) -> Task:
        task = self.get_task_by_id(task_id)

        if actor.role == UserRole.ADMIN:
            return task
        if actor.role == UserRole.MANAGER:
            if task.department_id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this task")
            return task
        if task.assignee_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this task")
        return task

    def update_task(self, actor: User, task_id: int, payload: TaskUpdate) -> Task:
        task = self.get_task_for_actor(actor, task_id)

        if actor.role == UserRole.STAFF and task.assignee_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this task")

        data = payload.model_dump(exclude_unset=True)

        if "department_id" in data:
            department = self.department_service.ensure_department_exists(data["department_id"])
            if actor.role == UserRole.MANAGER and department.id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to move task outside your department")
        else:
            department = self.department_service.ensure_department_exists(task.department_id)

        if "assignee_id" in data:
            assignee = self._get_user_or_404(data["assignee_id"])
            self._ensure_assignee_matches_department(assignee, data.get("department_id", task.department_id))
            if actor.role == UserRole.MANAGER and assignee.department_id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to assign tasks outside your department")

        for field, value in data.items():
            setattr(task, field, value)

        if payload.status == TaskStatus.DONE and task.done_at is None:
            task.done_at = datetime.now(UTC).replace(tzinfo=None)
        elif payload.status in {TaskStatus.TODO, TaskStatus.DOING, TaskStatus.BLOCKED}:
            task.done_at = None

        return self.repository.update(task)

    def delete_task(self, actor: User, task_id: int) -> None:
        task = self.get_task_for_actor(actor, task_id)

        if actor.role == UserRole.STAFF and task.assignee_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this task")

        self.repository.delete(task)

    def get_task_by_id(self, task_id: int) -> Task:
        task = self.repository.get_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def _ensure_assignee_matches_department(self, assignee: User, department_id: int) -> None:
        if assignee.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must belong to the same department as the task",
            )
