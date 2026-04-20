from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_authenticated_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthenticatedUserRead, LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    access_token = service.login(email=payload.email, password=payload.password)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=AuthenticatedUserRead)
def get_me(current_user: Annotated[User, Depends(require_authenticated_user)]) -> User:
    return current_user
