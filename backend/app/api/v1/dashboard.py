from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_manager_or_admin
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
def get_dashboard_data(
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """
    Return enterprise dashboard data scoped to the current admin or manager.
    """
    service = DashboardService(db)
    return service.get_dashboard_data(current_user)
