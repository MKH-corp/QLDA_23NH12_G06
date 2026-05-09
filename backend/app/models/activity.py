from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Ai là người thực hiện?
    
    action_type = Column(String(50), nullable=False, index=True) # VD: CREATE, UPDATE, DELETE, COMPLETE
    entity_type = Column(String(50), nullable=False, index=True) # VD: TASK, PROJECT, USER, KPI
    entity_id = Column(Integer, nullable=True, index=True)       # ID của đối tượng bị tác động
    
    description = Column(String(255), nullable=False) # Lời dịch hiển thị: "Đã tạo task mới"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Tránh N+1 bằng relationship
    user = relationship("User", lazy="joined")