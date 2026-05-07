from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Schema để tạo project mới. Chỉ cho phép các field hợp lệ."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None
    status: str = Field(default="planning", max_length=50)
    department_id: int | None = None


class ProjectUpdate(BaseModel):
    """Schema để cập nhật project. Tất cả field là optional."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=50)
    department_id: int | None = None


class ProjectRead(BaseModel):
    """Schema response trả về cho frontend."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    progress: float = 0.0
    total_tasks: int = 0