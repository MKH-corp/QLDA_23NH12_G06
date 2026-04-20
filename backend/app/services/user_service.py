from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.department_service import DepartmentService
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)
        self.department_service = DepartmentService(db)

    def create_user(self, payload: UserCreate) -> User:
        self._ensure_unique_email(payload.email)
        self.department_service.ensure_department_exists(payload.department_id)

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            role=payload.role,
            department_id=payload.department_id,
            is_active=payload.is_active,
        )
        return self.repository.create(user)

    def list_users(self, actor: User) -> list[User]:
        if actor.role == UserRole.ADMIN:
            return self.repository.list_all()
        if actor.role == UserRole.MANAGER:
            return self.repository.list_by_department(actor.department_id)
        return [actor]

    def get_user_for_actor(self, actor: User, user_id: int) -> User:
        user = self.get_user_by_id(user_id)

        if actor.role == UserRole.ADMIN:
            return user
        if actor.role == UserRole.MANAGER:
            if user.department_id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this user")
            return user
        if actor.id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this user")
        return user

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.get_user_by_id(user_id)
        data = payload.model_dump(exclude_unset=True)

        if "email" in data and data["email"] != user.email:
            self._ensure_unique_email(data["email"])
        if "department_id" in data:
            self.department_service.ensure_department_exists(data["department_id"])
        if "password" in data:
            data["password_hash"] = get_password_hash(data.pop("password"))

        for field, value in data.items():
            setattr(user, field, value)

        return self.repository.update(user)

    def delete_user(self, user_id: int) -> None:
        user = self.get_user_by_id(user_id)
        self.repository.delete(user)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def _ensure_unique_email(self, email: str) -> None:
        existing = self.repository.get_by_email(email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
