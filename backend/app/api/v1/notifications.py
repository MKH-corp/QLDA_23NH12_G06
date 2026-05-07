from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.notification import Notification

router = APIRouter()

@router.get("/")
def get_my_notifications(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    notes = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    return notes

@router.put("/{notif_id}/read")
def mark_as_read(notif_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    note = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if note:
        note.is_read = True
        db.commit()
    return {"status": "success"}