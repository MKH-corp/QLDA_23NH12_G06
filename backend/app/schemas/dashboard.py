from pydantic import BaseModel
from typing import List, Optional

class DashboardStats(BaseModel):
    total_employees: int
    active_departments: int
    completed_tasks: int
    avg_kpi: float

class DepartmentPerformance(BaseModel):
    id: int
    name: str
    score: float # Mức độ hoàn thành task của phòng ban

class UserPerformance(BaseModel):
    id: int
    full_name: str
    email: str
    department_name: str
    tasks_completed: int
    kpi_score: float

class ActivityLogResponse(BaseModel):
    id: int
    action: str
    description: str
    time_ago: str

class DashboardResponse(BaseModel):
    stats: DashboardStats
    department_charts: List[DepartmentPerformance]
    top_performers: List[UserPerformance]
    recent_activities: List[ActivityLogResponse]
    ai_insights: str
