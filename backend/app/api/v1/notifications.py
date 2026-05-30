from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.api.deps import get_db, require_authenticated_user
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.services.notification_engine import NotificationEngine
from app.schemas.notification import NotificationPageResponse

router = APIRouter()

@router.get("/", response_model=NotificationPageResponse)
def get_my_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_authenticated_user) # FIX: Chặn lỗi None.id
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    total = query.with_entities(func.count(Notification.id)).scalar() or 0
    unread_count = query.filter(Notification.is_read == False).with_entities(func.count(Notification.id)).scalar() or 0
    notifications = query.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return NotificationPageResponse(
        items=notifications,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )

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
            "message": "Đã kiểm tra thông báo của bạn",
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
            "message": "Đã kiểm tra thông báo của nhóm",
            "users_checked": len(team_users)
        }
    else:
        # Admin: check all
        engine.check_all()
        return {
            "message": "Đã kiểm tra thông báo toàn hệ thống",
            "users_checked": "all"
        }
