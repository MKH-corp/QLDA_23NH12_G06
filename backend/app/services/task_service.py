from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.project import Project
from app.models.user import User, UserRole
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.department_service import DepartmentService
from app.services.project_progress_engine import ProjectProgressEngine
# IMPORT HÀM LOGGING Ở ĐÂY
from app.utils.logger import log_system_activity
from app.services.kpi_engine import KpiEngine  # Để trigger KPI recalculation khi hoàn thành hoặc reopen task


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db  # Lưu lại db session để truyền vào logger
        self.repository = TaskRepository(db)
        self.user_repository = UserRepository(db)
        self.department_service = DepartmentService(db)

    def create_task(self, actor: User, payload: TaskCreate) -> Task:
        if actor.role == UserRole.STAFF:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff cannot create tasks")

        assignee = self._get_user_or_404(payload.assignee_id)
        department = self.department_service.ensure_department_exists(payload.department_id)
        self._ensure_assignee_matches_department(assignee, department.id)

        if actor.role == UserRole.MANAGER and department.id != actor.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create tasks outside your department")

        self._ensure_project_is_usable(payload.project_id, department.id, actor)

        task = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status,
            deadline=payload.deadline,
            base_weight=payload.base_weight,
            creator_id=actor.id,
            assignee_id=payload.assignee_id,
            reviewer_id=payload.reviewer_id or actor.id,
            department_id=payload.department_id,
            project_id=payload.project_id,
            estimated_hours=payload.estimated_hours,
            actual_hours=payload.actual_hours,
        )
        if task.status == TaskStatus.DONE and task.done_at is None:
            task.done_at = datetime.now(UTC).replace(tzinfo=None)
        created_task = self.repository.create(task)
        self._recalculate_kpi_for_users(created_task.assignee_id)
        self._recalculate_project_progress(created_task.project_id)

        # --- GHI LOG: TẠO TASK ---
        log_system_activity(
            db=self.db, user_id=actor.id, 
            action_type="CREATE", entity_type="TASK", entity_id=created_task.id, 
            description=f"Created a new task: {created_task.title}"
        )
        return created_task

    def list_tasks(
        self,
        actor: User,
        status: TaskStatus | None = None,
        overdue: bool | None = None,
        assignee_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:
        if actor.role == UserRole.ADMIN:
            return self.repository.list(status=status, overdue=overdue, assignee_id=assignee_id, page=page, page_size=page_size)
        if actor.role == UserRole.MANAGER:
            return self.repository.list(
                status=status,
                overdue=overdue,
                department_id=actor.department_id,
                assignee_id=assignee_id,
                page=page,
                page_size=page_size,
            )
        return self.repository.list(status=status, overdue=overdue, assignee_id=actor.id, page=page, page_size=page_size)

    def get_task_for_actor(self, actor: User, task_id: int) -> Task:
        task = self.get_task_by_id(task_id)

        if actor.role == UserRole.ADMIN:
            return task
        if actor.role == UserRole.MANAGER:
            if task.department_id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this task")
            return task
        if task.assignee_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this task")
        return task

    def update_task(self, actor: User, task_id: int, payload: TaskUpdate) -> Task:
        task = self.get_task_for_actor(actor, task_id)
        old_status = task.status
        old_assignee_id = task.assignee_id
        old_project_id = task.project_id

        if actor.role == UserRole.STAFF and task.assignee_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this task")

        data = payload.model_dump(exclude_unset=True)

        if "department_id" in data:
            department = self.department_service.ensure_department_exists(data["department_id"])
            if actor.role == UserRole.MANAGER and department.id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to move task outside your department")
        else:
            department = self.department_service.ensure_department_exists(task.department_id)

        if "assignee_id" in data:
            assignee = self._get_user_or_404(data["assignee_id"])
            self._ensure_assignee_matches_department(assignee, data.get("department_id", task.department_id))
            if actor.role == UserRole.MANAGER and assignee.department_id != actor.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to assign tasks outside your department")

        if "reviewer_id" in data and data["reviewer_id"] is not None:
            reviewer = self._get_user_or_404(data["reviewer_id"])
            self._ensure_assignee_matches_department(reviewer, data.get("department_id", task.department_id))

        if "project_id" in data:
            self._ensure_project_is_usable(data["project_id"], data.get("department_id", task.department_id), actor)

        for field, value in data.items():
            setattr(task, field, value)
        is_completed_now = False
        if payload.status == TaskStatus.DONE and task.done_at is None:
            task.done_at = datetime.now(UTC).replace(tzinfo=None)
            is_completed_now = True
        # ANTI-CHEATING: Phát hiện Reopen
        elif old_status == TaskStatus.DONE and payload.status is not None and payload.status != TaskStatus.DONE:
            task.done_at = None
            task.reopen_count = (task.reopen_count or 0) + 1
        elif old_status == TaskStatus.IN_REVIEW and payload.status in {TaskStatus.TODO, TaskStatus.DOING}:
            task.reopen_count = (task.reopen_count or 0) + 1

        updated_task = self.repository.update(task)

        # Recalculate snapshots for both users when assignment changes. This also
        # covers deadline and weight edits on already completed tasks.
        self._recalculate_kpi_for_users(old_assignee_id, updated_task.assignee_id)
        self._recalculate_project_progress(old_project_id, updated_task.project_id)

        # --- GHI LOG: CẬP NHẬT HOẶC HOÀN THÀNH TASK ---
        action = "COMPLETE" if is_completed_now else "UPDATE"
        desc = f"Completed task: {updated_task.title}" if is_completed_now else f"Updated task: {updated_task.title}"
        
        log_system_activity(
            db=self.db, user_id=actor.id, 
            action_type=action, entity_type="TASK", entity_id=updated_task.id, 
            description=desc
        )
        return updated_task

    def delete_task(self, actor: User, task_id: int) -> None:
        task = self.get_task_for_actor(actor, task_id)
        task_title = task.title
        assignee_id = task.assignee_id
        project_id = task.project_id

        if actor.role == UserRole.STAFF:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff cannot delete tasks")

        self.repository.delete(task)
        self._recalculate_kpi_for_users(assignee_id)
        self._recalculate_project_progress(project_id)

        # --- GHI LOG: XÓA TASK ---
        log_system_activity(
            db=self.db, user_id=actor.id, 
            action_type="DELETE", entity_type="TASK", entity_id=task_id, 
            description=f"Deleted task: {task_title}"
        )

    def get_task_by_id(self, task_id: int) -> Task:
        task = self.repository.get_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def _ensure_assignee_matches_department(self, assignee: User, department_id: int) -> None:
        if assignee.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must belong to the same department as the task",
            )

    def _ensure_project_is_usable(self, project_id: int | None, department_id: int, actor: User) -> None:
        if project_id is None:
            return

        project = self.db.get(Project, project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if project.department_id is not None and project.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project must belong to the same department as the task",
            )

        if actor.role == UserRole.MANAGER and project.department_id != actor.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to use projects outside your department",
            )

    def _recalculate_kpi_for_users(self, *user_ids: int) -> None:
        engine = KpiEngine(self.db)
        for user_id in set(user_ids):
            engine.recalculate_monthly_kpi(user_id)

    def _recalculate_project_progress(self, *project_ids: int | None) -> None:
        engine = ProjectProgressEngine(self.db)
        for project_id in {project_id for project_id in project_ids if project_id is not None}:
            project = self.db.get(Project, project_id)
            if project is not None:
                engine.calculate(project)
