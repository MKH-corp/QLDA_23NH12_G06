from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db, require_authenticated_user
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.services.notification_engine import NotificationEngine

router = APIRouter()

@router.get("/")
def get_my_notifications(
    skip: int = 0, 
    limit: int = 50,
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_authenticated_user) # FIX: Chặn lỗi None.id
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
    
    return notifications

@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo"
        )

    notification.is_read = True
    db.commit()

    return {"message": "Đã đánh dấu đọc", "id": notification.id}


@router.post("/run-check")
def run_notification_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """
    Run notification checks.
    - staff: check for self only
    - manager: check for team/department
    - admin: check for all
    """
    engine = NotificationEngine(db)

    if current_user.role == UserRole.STAFF:
        # Staff: check only self
        engine.check_user(current_user.id)
        return {
            "message": "Notification check completed for yourself",
            "users_checked": 1
        }
    elif current_user.role == UserRole.MANAGER:
        # Manager: check team in their department
        team_users = db.query(User).filter(
            User.department_id == current_user.department_id,
            User.is_active == True
        ).all()
        for user in team_users:
            engine.check_user(user.id)
        return {
            "message": "Notification check completed for your team",
            "users_checked": len(team_users)
        }
    else:
        # Admin: check all
        engine.check_all()
        return {
            "message": "Notification check completed for all users",
            "users_checked": "all"
        }
