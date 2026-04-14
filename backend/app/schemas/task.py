from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    deadline: date | None = None
    base_weight: int = 1
    creator_id: int
    assignee_id: int
    department_id: int


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    deadline: date | None = None
    base_weight: int | None = None
    creator_id: int | None = None
    assignee_id: int | None = None
    department_id: int | None = None


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
    department_id: int
