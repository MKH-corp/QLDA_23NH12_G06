import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
        index=True,
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    base_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    creator: Mapped["User"] = relationship(back_populates="created_tasks", foreign_keys=[creator_id])
    assignee: Mapped["User"] = relationship(back_populates="assigned_tasks", foreign_keys=[assignee_id])
    department: Mapped["Department"] = relationship(back_populates="tasks")