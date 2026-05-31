from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.project import Project
from app.models.task import Task
from app.models.user import User, UserRole
from app.repositories.department_repository import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DepartmentRepository(db)

    def create_department(self, payload: DepartmentCreate) -> Department:
        self._ensure_unique_name(payload.name)
        department = Department(name=payload.name)
        return self.repository.create(department)

    def list_departments(self, actor: User) -> list[Department]:
        if actor.role == UserRole.ADMIN:
            return self.repository.list()
        return [self.get_department_for_actor(actor, actor.department_id)]

    def get_department_for_actor(self, actor: User, department_id: int) -> Department:
        department = self.repository.get_by_id(department_id)
        if department is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        if actor.role == UserRole.ADMIN:
            return department

        if department.id != actor.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this department")

        return department

    def update_department(self, department_id: int, payload: DepartmentUpdate) -> Department:
        department = self.get_department_by_id(department_id)
        if payload.name != department.name:
            self._ensure_unique_name(payload.name)
        department.name = payload.name
        return self.repository.update(department)

    def delete_department(self, department_id: int) -> None:
        department = self.get_department_by_id(department_id)
        self._ensure_department_can_be_deleted(department.id)
        self.repository.delete(department)

    def get_department_by_id(self, department_id: int) -> Department:
        department = self.repository.get_by_id(department_id)
        if department is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        return department

    def ensure_department_exists(self, department_id: int) -> Department:
        return self.get_department_by_id(department_id)

    def _ensure_unique_name(self, name: str) -> None:
        existing = self.repository.get_by_name(name)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name already exists")

    def _ensure_department_can_be_deleted(self, department_id: int) -> None:
        users_count = self.db.query(User).filter(User.department_id == department_id).count()
        tasks_count = self.db.query(Task).filter(Task.department_id == department_id).count()
        projects_count = self.db.query(Project).filter(Project.department_id == department_id).count()
        if users_count or tasks_count or projects_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department cannot be deleted while users, tasks, or projects still reference it",
            )
