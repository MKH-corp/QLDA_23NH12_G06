from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.utils.logger import log_system_activity


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def get_projects(self, department_id: int | None = None) -> list[dict]:
        query = self.db.query(Project)
        if department_id:
            query = query.filter(Project.department_id == department_id)

        projects = query.all()
        result = []

        for p in projects:
            total_tasks = self.db.query(Task).filter(Task.project_id == p.id).count()
            done_tasks = self.db.query(Task).filter(
                Task.project_id == p.id,
                Task.status == 'done',
            ).count()
            progress = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0

            result.append({
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "progress": round(progress, 1),
                "total_tasks": total_tasks,
            })

        return result

    # THÊM current_user_id VÀO THAM SỐ VÀ SỬA TYPE HINT THÀNH dict
    def create_project(self, payload: ProjectCreate, current_user_id: int) -> dict:
        """
        Tạo project mới từ validated schema.
        Chỉ các field trong ProjectCreate mới được ghi vào DB.
        """
        new_project = Project(
            name=payload.name,
            description=payload.description,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status,
            department_id=payload.department_id,
        )
        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        
        # [AUTO LOGGING]
        log_system_activity(
            db=self.db, user_id=current_user_id, 
            action_type="CREATE", entity_type="PROJECT", entity_id=new_project.id, 
            description=f"Created new project: {new_project.name}"
        )
        
        return {
            "id": new_project.id,
            "name": new_project.name,
            "status": new_project.status,
            "progress": 0,       # Project mới tạo dĩ nhiên progress là 0%
            "total_tasks": 0     # Project mới tạo chưa có task nào
        }

    # THÊM current_user_id VÀO THAM SỐ
    def update_project(self, project: Project, payload: ProjectUpdate, current_user_id: int) -> Project:
        """
        Cập nhật project từ validated schema.
        Chỉ các field được set trong payload mới được cập nhật (exclude_unset).
        """
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(project, field, value)
            
        self.db.commit()
        self.db.refresh(project)
        
        # [AUTO LOGGING]
        log_system_activity(
            db=self.db, user_id=current_user_id, 
            action_type="UPDATE", entity_type="PROJECT", entity_id=project.id, 
            description=f"Updated project: {project.name}"
        )
        
        return project