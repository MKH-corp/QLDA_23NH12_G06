from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthenticatedUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: UserRole
    department_id: int
    is_active: bool
    created_at: datetime
