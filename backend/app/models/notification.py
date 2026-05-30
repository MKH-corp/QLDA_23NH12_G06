from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String(1000))
    type = Column(String(50), default="info")  # info, warning, success, danger
    severity = Column(String(50), default="info")  # info, success, warning, danger
    source = Column(String(50), default="system")  # system, notification_engine, ai
    metadata_json = Column(JSON, nullable=True)  # {task_ids: [], overdue_count: 0, ...}
    is_ai_generated = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
