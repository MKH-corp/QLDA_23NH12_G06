from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db, require_authenticated_user # FIX: Import đúng dependency chặn Token
from app.models.notification import Notification
from app.models.user import User

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
    current_user: User = Depends(require_authenticated_user) # FIX: Chặn lỗi None.id
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