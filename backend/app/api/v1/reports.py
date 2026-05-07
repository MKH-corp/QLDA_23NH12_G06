from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, require_authenticated_user  # Sửa thêm ở issue 5, tạm giữ nguyên
from app.models.task import Task
from app.models.department import Department
from app.models.user import User

router = APIRouter()


@router.get("/productivity")
def get_productivity_report(
    db: Session = Depends(get_db),
    current_user=Depends(require_authenticated_user),  # Sẽ xử lý đầy đủ ở issue 5
):
    """API xuất báo cáo năng suất theo phòng ban"""
    departments = db.query(Department).all()
    report = []

    for dept in departments:
        total = db.query(Task).filter(Task.department_id == dept.id).count()
        done = db.query(Task).filter(
            Task.department_id == dept.id,
            Task.status == "done",
        ).count()

        # FIX: Đổi Task.due_date -> Task.deadline (tên đúng trong SQLAlchemy model)
        overdue = db.query(Task).filter(
            Task.department_id == dept.id,
            Task.status != "done",
            Task.deadline.isnot(None),          # Kiểm tra deadline không null trước
            Task.deadline < func.current_date(), # So sánh với ngày hiện tại
        ).count()

        report.append({
            "department_name": dept.name,
            "total_tasks": total,
            "completed": done,
            "overdue": overdue,
            "productivity_score": round((done / total * 100) if total > 0 else 0, 1),
        })

    # Sắp xếp theo năng suất giảm dần
    report.sort(key=lambda x: x["productivity_score"], reverse=True)
    return report