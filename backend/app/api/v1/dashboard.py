from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
def get_dashboard_data(
    _: Annotated[User, Depends(require_authenticated_user)],
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """
    Lấy toàn bộ dữ liệu tổng hợp cho Enterprise Dashboard.
    Yêu cầu đăng nhập. Dữ liệu hiển thị không lọc theo role
    vì đây là trang tổng quan dành cho admin/manager.
    """
    service = DashboardService(db)
    return service.get_dashboard_data()