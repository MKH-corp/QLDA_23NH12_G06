from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.departments import router as departments_router
from app.api.v1.references import router as references_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.users import router as users_router
from app.api.v1 import dashboard
from app.api.v1 import projects, kpi, notifications
from app.api.v1.reports import router as reports_router
from app.api.v1.activities import router as activities_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(references_router)
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(departments_router)
api_router.include_router(users_router)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(kpi.router, prefix="/kpi", tags=["kpi"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(activities_router, prefix="/activities", tags=["activities"])
