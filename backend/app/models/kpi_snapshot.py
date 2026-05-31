from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base

class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "period_type", "period_key", name="uq_kpi_snapshot_user_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    period_type = Column(String(20), default="MONTHLY") # DAILY, WEEKLY, MONTHLY
    period_key = Column(String(20), nullable=False, index=True) # VD: "2026-05"
    
    total_score = Column(Float, default=0.0)
    tasks_completed = Column(Integer, default=0)
    tasks_overdue = Column(Integer, default=0)
    
    breakdown = Column(JSON, nullable=True) # EXPLAINABILITY: {"base": 80, "penalty": -10}
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
