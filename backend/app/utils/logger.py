from sqlalchemy.orm import Session
from app.models.activity import ActivityLog

def log_system_activity(
    db: Session, 
    user_id: int, 
    action_type: str, 
    entity_type: str, 
    entity_id: int, 
    description: str
):
    """
    Centralized logging utility. Được gọi ngầm ở Service Layer sau khi commit thành công.
    """
    try:
        activity = ActivityLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description
        )
        db.add(activity)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Log Error]: Failed to write activity log - {str(e)}")
        # Không throw exception ra ngoài để tránh làm crash tác vụ chính của User