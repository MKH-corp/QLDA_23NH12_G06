from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.task import Task
from fastapi import HTTPException

class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def get_projects(self, department_id: int = None):
        query = self.db.query(Project)
        if department_id:
            query = query.filter(Project.department_id == department_id)
        
        projects = query.all()
        # Tính toán progress (Analytics)
        result = []
        for p in projects:
            total_tasks = self.db.query(Task).filter(Task.project_id == p.id).count()
            done_tasks = self.db.query(Task).filter(Task.project_id == p.id, Task.status == 'done').count()
            progress = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            result.append({
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "progress": round(progress, 1),
                "total_tasks": total_tasks
            })
        return result

    def create_project(self, data: dict):
        new_project = Project(**data)
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return new_project