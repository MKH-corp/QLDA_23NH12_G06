from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.reference import DepartmentRead, UserRead

router = APIRouter(prefix="/references", tags=["references"])


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db)) -> list[Department]:
    stmt = select(Department).order_by(Department.name.asc())
    return list(db.scalars(stmt).all())


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    stmt = select(User).order_by(User.full_name.asc())
    return list(db.scalars(stmt).all())
