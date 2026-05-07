from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.task import Task
from app.models.user import User
from app.models.kpi_record import KpiRecord
from datetime import datetime

router = APIRouter()

@router.get("/analytics")
def get_kpi_analytics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """API cho trang KPI Tracking và Report"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    users = db.query(User).filter(User.is_active == True).all()
    results = []
    
    for u in users:
        # 1. Tính KPI Tức thời (Current Month)
        # Thực tế bạn sẽ query task.updated_at nằm trong tháng hiện tại
        assigned = db.query(Task).filter(Task.assignee_id == u.id).count()
        completed = db.query(Task).filter(Task.assignee_id == u.id, Task.status == 'done').count()
        
        # Công thức: (Hoàn thành / Được giao) - Phạt task overdue
        base_score = (completed / assigned * 100) if assigned > 0 else 0
        
        # 2. Lấy History các tháng trước
        history = db.query(KpiRecord).filter(KpiRecord.user_id == u.id).order_by(KpiRecord.month.desc()).limit(3).all()
        
        results.append({
            "user_id": u.id,
            "name": u.full_name,
            "department_id": u.department_id,
            "current_month_kpi": round(base_score, 1),
            "tasks_done": completed,
            "history": [{"month": h.month, "score": h.score} for h in history]
        })
        
    # Sắp xếp để làm Ranking Table
    results.sort(key=lambda x: x['current_month_kpi'], reverse=True)
    return results