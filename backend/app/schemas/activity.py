from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str] = None # Lấy từ relationship
    action_type: str
    entity_type: str
    entity_id: Optional[int]
    description: str
    created_at: datetime
    time_ago: Optional[str] = None

    class Config:
        from_attributes = True

class ActivityListResponse(BaseModel):
    total: int
    data: List[ActivityLogResponse]