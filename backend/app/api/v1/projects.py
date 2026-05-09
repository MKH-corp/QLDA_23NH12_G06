from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/")
def get_all_projects(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(require_authenticated_user)] = None,
) -> list:
    service = ProjectService(db)
    dept_id = current_user.department_id if current_user.role == UserRole.MANAGER else None
    return service.get_projects(department_id=dept_id)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,  
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(require_authenticated_user)] = None,
) -> dict:
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không đủ quyền thực hiện thao tác này",
        )
    service = ProjectService(db)
    # FIX: Truyền thêm current_user.id vào service
    return service.create_project(payload, current_user.id)


@router.put("/{project_id}")
def update_project(
    project_id: int,
    payload: ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(require_authenticated_user)] = None,
) -> dict:
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không đủ quyền thực hiện thao tác này",
        )
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy project",
        )
    service = ProjectService(db)
    # FIX: Truyền thêm current_user.id vào service
    return service.update_project(project, payload, current_user.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(require_authenticated_user)] = None,
) -> None:
    if current_user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không đủ quyền thực hiện thao tác này",
        )
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy project",
        )
    db.delete(project)
    db.commit()
    