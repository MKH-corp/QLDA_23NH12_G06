from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repository = UserRepository(db)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if user is None or not user.password_hash or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

        return user

    def login(self, email: str, password: str) -> str:
        user = self.authenticate_user(email, password)
        return create_access_token(subject=str(user.id), email=user.email, role=user.role.value)
