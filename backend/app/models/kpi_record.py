from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class KpiRecord(Base):
    __tablename__ = "kpi_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    score = Column(Float, nullable=False) # Điểm chốt của tháng
    tasks_completed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())