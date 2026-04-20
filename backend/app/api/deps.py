from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import JWTError, decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


credentials_dependency = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
db_dependency = Annotated[Session, Depends(get_db)]


def get_current_user(credentials: credentials_dependency, db: db_dependency) -> User | None:
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if subject is None:
            return None
        user_id = int(subject)
    except (JWTError, ValueError, TypeError):
        return None

    repository = UserRepository(db)
    return repository.get_by_id(user_id)


def require_authenticated_user(current_user: Annotated[User | None, Depends(get_current_user)]) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    return current_user


def require_admin(current_user: Annotated[User, Depends(require_authenticated_user)]) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_manager_or_admin(current_user: Annotated[User, Depends(require_authenticated_user)]) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or admin role required")
    return current_user

