from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class KpiSnapshotResponse(BaseModel):
    user_id: int
    period_type: str
    period_key: str
    total_score: float
    tasks_completed: int
    tasks_overdue: int
    breakdown: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True

class KpiRankingResponse(BaseModel):
    user_id: int
    full_name: str
    department_name: str
    total_score: float
    tasks_completed: int