from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AIEvidenceSchema(BaseModel):
    kpi_score: Optional[float] = None
    task_ids: List[int] = []
    overdue_count: int = 0
    near_deadline_count: int = 0
    blocked_count: int = 0
    tasks_completed: int = 0


class AIInsightSchema(BaseModel):
    type: str  # warning, info, success, danger
    title: str
    message: str
    severity: str  # info, success, warning, danger
    recommendations: List[str] = []
    evidence: AIEvidenceSchema


class AIDashboardSummarySchema(BaseModel):
    user_id: int
    role: str
    total_kpi_score: Optional[float] = None
    total_tasks_completed: int = 0
    overdue_tasks: int = 0
    near_deadline_tasks: int = 0
    blocked_tasks: int = 0
    risk_users: List[Dict[str, Any]] = []
    top_performers: List[Dict[str, Any]] = []
    team_overdue_count: int = 0
    recommendations: List[str] = []


class AIChatRequestSchema(BaseModel):
    message: str


class AIChatResponseSchema(BaseModel):
    reply: str
    insights: List[str] = []
    used_fallback: bool = False
    evidence: Dict[str, Any] = {}
