from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.department import Department


class DepartmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, department: Department) -> Department:
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def get_by_id(self, department_id: int) -> Department | None:
        return self.db.get(Department, department_id)

    def get_by_name(self, name: str) -> Department | None:
        stmt: Select[tuple[Department]] = select(Department).where(Department.name == name)
        return self.db.scalar(stmt)

    def list(self) -> list[Department]:
        stmt: Select[tuple[Department]] = select(Department).order_by(Department.name.asc())
        return list(self.db.scalars(stmt).all())

    def update(self, department: Department) -> Department:
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete(self, department: Department) -> None:
        self.db.delete(department)
        self.db.commit()
