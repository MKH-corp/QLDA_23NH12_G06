from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.department_service import DepartmentService
from app.schemas.user import UserCreate, UserUpdate
# IMPORT HÀM LOGGING Ở ĐÂY
from app.utils.logger import log_system_activity


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db # Lưu session để ghi log
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
        created_user = self.repository.create(user)

        # --- GHI LOG: TẠO NHÂN VIÊN ---
        log_system_activity(
            db=self.db, user_id=None, # Set None (System) nếu Controller chưa truyền xuống current_user
            action_type="CREATE", entity_type="USER", entity_id=created_user.id, 
            description=f"Created new employee profile: {created_user.full_name}"
        )

        return created_user

    def list_users(self, actor: User) -> list[User]:
        if actor.role == UserRole.ADMIN:
            return self.repository.list_all()
        if actor.role == UserRole.MANAGER:
            return self.repository.list_by_department(actor.department_id)
        return [actor]

    def search_users(
        self, 
        actor: User, 
        search_query: str = "",
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[User], int]:
        """Search users based on actor's role."""
        if actor.role == UserRole.ADMIN:
            users, total = self.repository.search(search_query, skip=skip, limit=limit)
            return users, total
        if actor.role == UserRole.MANAGER:
            users, total = self.repository.search(search_query, department_id=actor.department_id, skip=skip, limit=limit)
            return users, total
        # For STAFF, only return self
        if search_query.lower() in actor.full_name.lower() or search_query.lower() in actor.email.lower():
            return [actor], 1
        return [], 0

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

        updated_user = self.repository.update(user)

        # --- GHI LOG: CẬP NHẬT NHÂN VIÊN ---
        log_system_activity(
            db=self.db, user_id=None,
            action_type="UPDATE", entity_type="USER", entity_id=updated_user.id, 
            description=f"Updated employee profile: {updated_user.email}"
        )

        return updated_user

    def delete_user(self, user_id: int) -> None:
        user = self.get_user_by_id(user_id)
        user_email = user.email
        
        self.repository.delete(user)

        # --- GHI LOG: XÓA NHÂN VIÊN ---
        log_system_activity(
            db=self.db, user_id=None,
            action_type="DELETE", entity_type="USER", entity_id=user_id, 
            description=f"Deleted/Disabled employee: {user_email}"
        )

    def get_user_by_id(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def _ensure_unique_email(self, email: str) -> None:
        existing = self.repository.get_by_email(email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
