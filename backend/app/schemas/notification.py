from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PageResponse


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str | None
    type: str
    severity: str
    source: str
    metadata_json: dict | None
    is_ai_generated: bool
    is_read: bool
    created_at: datetime


class NotificationPageResponse(PageResponse[NotificationRead]):
    unread_count: int
