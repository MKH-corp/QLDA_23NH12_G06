from app.models.project import Project
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.project_service import ProjectService

router = APIRouter()

@router.get("/")
def get_all_projects(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = ProjectService(db)
    # Nếu là manager, chỉ lấy project của phòng ban mình
    dept_id = current_user.department_id if current_user.role == 'manager' else None
    return service.get_projects(department_id=dept_id)

@router.post("/")
def create_project(data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    service = ProjectService(db)
    return service.create_project(data)
from fastapi import HTTPException

@router.put("/{project_id}")
def update_project(project_id: int, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = ProjectService(db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}