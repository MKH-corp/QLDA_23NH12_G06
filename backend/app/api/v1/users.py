from typing import Annotated

from fastapi import APIRouter, Depends, Response, status, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_authenticated_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    user = service.create_user(payload)
    return {
    "id": user.id,
    "full_name": user.full_name,
    "email": user.email,
    "role": user.role,
    "department_id": user.department_id,
    "is_active": user.is_active,
    "created_at": user.created_at,
    "department_name": user.department.name if user.department else "N/A"
}


@router.get("", response_model=list[UserRead])
def list_users(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    search: str = Query("", description="Search by name or email"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    service = UserService(db)
    users, _ = service.search_users(current_user, search_query=search, skip=skip, limit=limit)
    return [
        UserRead.model_validate({**u.__dict__, "department_name": u.department.name})
        for u in users
    ]


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    user = service.get_user_for_actor(current_user, user_id)
    return UserRead.model_validate({**user.__dict__, "department_name": user.department.name})


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    user = service.update_user(user_id, payload)
    return {
    "id": user.id,
    "full_name": user.full_name,
    "email": user.email,
    "role": user.role,
    "department_id": user.department_id,
    "is_active": user.is_active,
    "created_at": user.created_at,
    "department_name": user.department.name if user.department else "N/A"
}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> Response:
    service = UserService(db)
    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
