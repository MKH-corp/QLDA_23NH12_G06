from fastapi import APIRouter

from app.api.v1.references import router as references_router
from app.api.v1.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(tasks_router)
api_router.include_router(references_router)
