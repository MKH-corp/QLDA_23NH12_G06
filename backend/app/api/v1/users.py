from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
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
    return service.create_user(payload)


@router.get("", response_model=list[UserRead])
def list_users(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> list[UserRead]:
    service = UserService(db)
    return service.list_users(current_user)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    return service.get_user_for_actor(current_user, user_id)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> UserRead:
    service = UserService(db)
    return service.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> Response:
    service = UserService(db)
    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
