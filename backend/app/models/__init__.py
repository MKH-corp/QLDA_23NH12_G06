from app.models.department import Department
from app.models.task import Task, TaskStatus
from app.models.user import User
# --- THÊM 3 DÒNG NÀY VÀO DƯỚI CÙNG ---
from app.models.project import Project
from app.models.kpi_record import KpiRecord
from app.models.notification import Notification
__all__ = ["Department", "User", "Task", "TaskStatus", "Project", "KpiRecord", "Notification"]
