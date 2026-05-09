from sqlalchemy import Column, Integer, String, Float, Boolean
from app.db.base import Base

class KpiRule(Base):
    __tablename__ = "kpi_rules"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False) # VD: ON_TIME_BONUS, OVERDUE_PENALTY
    description = Column(String(255))
    multiplier = Column(Float, default=1.0) # Trọng số
    is_active = Column(Boolean, default=True)