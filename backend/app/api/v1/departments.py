from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_authenticated_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    return service.create_department(payload)


@router.get("", response_model=list[DepartmentRead])
def list_departments(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> list[DepartmentRead]:
    service = DepartmentService(db)
    return service.list_departments(current_user)


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(
    department_id: int,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    return service.get_department_for_actor(current_user, department_id)


@router.put("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> DepartmentRead:
    service = DepartmentService(db)
    return service.update_department(department_id, payload)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> Response:
    service = DepartmentService(db)
    service.delete_department(department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
