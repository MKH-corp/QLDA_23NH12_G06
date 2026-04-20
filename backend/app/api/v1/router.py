from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.departments import router as departments_router
from app.api.v1.references import router as references_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(references_router)
api_router.include_router(departments_router)
api_router.include_router(users_router)
