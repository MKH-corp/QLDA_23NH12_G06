from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class AIEvidenceSchema(BaseModel):
    kpi_score: Optional[float] = None
    task_ids: List[int] = Field(default_factory=list)
    overdue_count: int = 0
    near_deadline_count: int = 0
    blocked_count: int = 0
    tasks_completed: int = 0


class AIInsightSchema(BaseModel):
    type: str  # warning, info, success, danger
    title: str
    message: str
    severity: str  # info, success, warning, danger
    recommendations: List[str] = Field(default_factory=list)
    evidence: AIEvidenceSchema


class AIDashboardSummarySchema(BaseModel):
    user_id: int
    role: str
    total_kpi_score: Optional[float] = None
    total_tasks_completed: int = 0
    overdue_tasks: int = 0
    near_deadline_tasks: int = 0
    blocked_tasks: int = 0
    risk_users: List[Dict[str, Any]] = Field(default_factory=list)
    top_performers: List[Dict[str, Any]] = Field(default_factory=list)
    team_overdue_count: int = 0
    recommendations: List[str] = Field(default_factory=list)


class AIChatMessageSchema(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class AIChatRequestSchema(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: List[AIChatMessageSchema] = Field(default_factory=list, max_length=8)


class AIChatResponseSchema(BaseModel):
    reply: str
    insights: List[str] = Field(default_factory=list)
    used_fallback: bool = False
    evidence: Dict[str, Any] = Field(default_factory=dict)
