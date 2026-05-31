from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    deadline: date | None = None
    base_weight: int = Field(default=1, ge=1, le=10)
    assignee_id: int
    reviewer_id: int | None = None
    department_id: int
    project_id: int | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    actual_hours: float = Field(default=0, ge=0)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    deadline: date | None = None
    base_weight: int | None = Field(default=None, ge=1, le=10)
    assignee_id: int | None = None
    reviewer_id: int | None = None
    department_id: int | None = None
    project_id: int | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    actual_hours: float | None = Field(default=None, ge=0)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    deadline: date | None
    done_at: datetime | None
    base_weight: int
    creator_id: int
    assignee_id: int
    reviewer_id: int | None = None
    department_id: int
    project_id: int | None = None
    estimated_hours: float | None = None
    actual_hours: float = 0
