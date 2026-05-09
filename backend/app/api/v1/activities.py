from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.deps import get_db, get_current_user
from app.models.activity import ActivityLog
from app.schemas.activity import ActivityListResponse, ActivityLogResponse
from datetime import datetime, timezone

router = APIRouter()

def get_time_ago(dt: datetime) -> str:
    # Helper format time
    if not dt: return ""
    now = datetime.now(timezone.utc)
    diff = now - dt.replace(tzinfo=timezone.utc)
    seconds = diff.total_seconds()
    
    if seconds < 60: return "Just now"
    if seconds < 3600: return f"{int(seconds//60)} mins ago"
    if seconds < 86400: return f"{int(seconds//3600)} hours ago"
    return f"{int(seconds//86400)} days ago"

@router.get("/recent", response_model=ActivityListResponse)
def get_recent_activities(limit: int = 10, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Tối ưu N+1 bằng joinedload user (nếu cần thiết, hoặc user backref mặc định là joined)
    logs = db.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(limit).all()
    
    results = []
    for log in logs:
        user_name = log.user.full_name if log.user else "System"
        results.append(ActivityLogResponse(
            id=log.id, user_id=log.user_id, user_name=user_name,
            action_type=log.action_type, entity_type=log.entity_type,
            entity_id=log.entity_id, description=log.description,
            created_at=log.created_at, time_ago=get_time_ago(log.created_at)
        ))
        
    return ActivityListResponse(total=len(results), data=results)