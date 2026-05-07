from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.task import Task
from app.models.department import Department
from sqlalchemy import func

router = APIRouter()

@router.get("/productivity")
def get_productivity_report(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """API xuất báo cáo năng suất theo phòng ban"""
    departments = db.query(Department).all()
    report = []
    
    for dept in departments:
        total = db.query(Task).filter(Task.department_id == dept.id).count()
        done = db.query(Task).filter(Task.department_id == dept.id, Task.status == 'done').count()
        overdue = db.query(Task).filter(Task.department_id == dept.id, Task.status != 'done', Task.due_date < func.now()).count()
        
        report.append({
            "department_name": dept.name,
            "total_tasks": total,
            "completed": done,
            "overdue": overdue,
            "productivity_score": round((done / total * 100) if total > 0 else 0, 1)
        })
    
    # Sắp xếp theo năng suất giảm dần
    report.sort(key=lambda x: x["productivity_score"], reverse=True)
    return report