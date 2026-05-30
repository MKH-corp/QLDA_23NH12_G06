from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.deps import get_db, get_current_user
from app.models.kpi_snapshot import KpiSnapshot
from app.models.user import User, UserRole
from app.schemas.kpi import KpiSnapshotResponse, KpiRankingResponse
from datetime import datetime
from app.api.deps import get_db, require_authenticated_user
from fastapi import HTTPException

router = APIRouter()

@router.get("/me", response_model=KpiSnapshotResponse)
def get_my_kpi(db=Depends(get_db), current_user: User = Depends(require_authenticated_user)):
    period_key = f"{datetime.now().year}-{datetime.now().month:02d}"
    snapshot = db.query(KpiSnapshot).filter(
        KpiSnapshot.user_id == current_user.id,
        KpiSnapshot.period_key == period_key
    ).first()
    
    if not snapshot: # Empty state fallback
        return KpiSnapshotResponse(user_id=current_user.id, period_type="MONTHLY", period_key=period_key, total_score=0, tasks_completed=0, tasks_overdue=0, breakdown={}, updated_at=datetime.now())
    return snapshot

@router.get("/team", response_model=list[KpiRankingResponse])
def get_team_kpi(db=Depends(get_db), current_user: User = Depends(require_authenticated_user)):
    """Role-based visibility: Admin thấy hết, Manager thấy team mình"""
    period_key = f"{datetime.now().year}-{datetime.now().month:02d}"
    
    query = db.query(KpiSnapshot, User).join(User, KpiSnapshot.user_id == User.id)\
              .filter(KpiSnapshot.period_key == period_key)
              
    if current_user.role == UserRole.MANAGER:
        query = query.filter(User.department_id == current_user.department_id)
    elif current_user.role == UserRole.STAFF:
        query = query.filter(User.id == current_user.id)
        
    results = query.order_by(desc(KpiSnapshot.total_score)).limit(10).all()
    
    return [
        KpiRankingResponse(
            user_id=u.id, full_name=u.full_name, department_name=u.department.name if u.department else "N/A",
            total_score=snap.total_score, tasks_completed=snap.tasks_completed
        ) for snap, u in results
    ]
@router.get("/{user_id}", response_model=KpiSnapshotResponse)
def get_user_kpi(user_id: int, db=Depends(get_db), current_user: User = Depends(require_authenticated_user)):
    """API lấy điểm KPI của một nhân viên cụ thể dành cho Manager/Admin"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Bảo mật: Kiểm tra quyền truy cập
    if current_user.role == UserRole.STAFF and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Không được phép xem KPI người khác")
    if current_user.role == UserRole.MANAGER and target_user.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Không được phép xem KPI của phòng ban khác")

    period_key = f"{datetime.now().year}-{datetime.now().month:02d}"
    snapshot = db.query(KpiSnapshot).filter(
        KpiSnapshot.user_id == user_id,
        KpiSnapshot.period_key == period_key
    ).first()
    
    # Fallback nếu nhân viên chưa có điểm
    if not snapshot: 
        return KpiSnapshotResponse(
            user_id=user_id, period_type="MONTHLY", period_key=period_key, 
            total_score=0, tasks_completed=0, tasks_overdue=0, breakdown={}, updated_at=datetime.now()
        )
    return snapshot
