from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.models.department import Department
from app.models.task import Task
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/productivity")
def get_productivity_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user),
):
    departments_query = db.query(Department)
    if current_user.role != UserRole.ADMIN:
        departments_query = departments_query.filter(Department.id == current_user.department_id)

    report = []
    for dept in departments_query.all():
        task_filters = [Task.department_id == dept.id]
        if current_user.role == UserRole.STAFF:
            task_filters.append(Task.assignee_id == current_user.id)

        total = db.query(Task).filter(*task_filters).count()
        done = db.query(Task).filter(*task_filters, Task.status == "done").count()
        overdue = db.query(Task).filter(
            *task_filters,
            Task.status != "done",
            Task.deadline.isnot(None),
            Task.deadline < func.current_date(),
        ).count()

        report.append(
            {
                "department_name": dept.name,
                "total_tasks": total,
                "completed": done,
                "overdue": overdue,
                "productivity_score": round((done / total * 100) if total > 0 else 0, 1),
            }
        )

    report.sort(key=lambda item: item["productivity_score"], reverse=True)
    return report
