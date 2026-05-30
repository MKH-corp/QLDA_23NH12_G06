from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_authenticated_user
from app.models.activity import ActivityLog
from app.models.user import User, UserRole
from app.schemas.activity import ActivityListResponse, ActivityLogResponse

router = APIRouter()


def get_time_ago(created_at: datetime | None) -> str:
    if created_at is None:
        return ""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
    if seconds < 60:
        return "Vừa xong"
    if seconds < 3600:
        return f"{int(seconds // 60)} phút trước"
    if seconds < 86400:
        return f"{int(seconds // 3600)} giờ trước"
    return f"{int(seconds // 86400)} ngày trước"


@router.get("/recent", response_model=ActivityListResponse)
def get_recent_activities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user),
) -> ActivityListResponse:
    query = db.query(ActivityLog)
    if current_user.role == UserRole.MANAGER:
        query = query.join(User, ActivityLog.user_id == User.id).filter(
            User.department_id == current_user.department_id
        )
    elif current_user.role == UserRole.STAFF:
        query = query.filter(ActivityLog.user_id == current_user.id)

    total = query.with_entities(func.count(ActivityLog.id)).scalar() or 0
    logs = (
        query.options(joinedload(ActivityLog.user))
        .order_by(desc(ActivityLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    results = [
        ActivityLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.full_name if log.user else "System",
            action_type=log.action_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            description=log.description,
            created_at=log.created_at,
            time_ago=get_time_ago(log.created_at),
        )
        for log in logs
    ]
    return ActivityListResponse(
        total=total,
        data=results,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
