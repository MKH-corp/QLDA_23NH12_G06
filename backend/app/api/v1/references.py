from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_authenticated_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.department import DepartmentRead
from app.schemas.user import UserRead
from app.services.department_service import DepartmentService
from app.services.user_service import UserService

router = APIRouter(prefix="/references", tags=["references"])


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> list[DepartmentRead]:
    department_service = DepartmentService(db)
    return department_service.list_departments(current_user)


@router.get("/users", response_model=list[UserRead])
def list_users(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> list[UserRead]:
    user_service = UserService(db)
    return user_service.list_users(current_user)
