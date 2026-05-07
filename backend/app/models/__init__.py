from app.models.department import Department
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.models.kpi_record import KpiRecord
from app.models.notification import Notification
from app.models.activity import ActivityLog  # Thêm để Alembic tracking đúng

__all__ = [
    "Department",
    "User",
    "Task",
    "TaskStatus",
    "Project",
    "KpiRecord",
    "Notification",
    "ActivityLog",
]