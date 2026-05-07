from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50), default="planning") # planning, active, completed, on_hold
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # Quan hệ với Task (Bạn cần vào file models/task.py thêm cột project_id = Column(Integer, ForeignKey("projects.id"), nullable=True))
    tasks = relationship("Task", back_populates="project")