from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db import models  # noqa: F401
from app.db.base import Base
from app.models.activity import ActivityLog
from app.models.department import Department
from app.models.kpi_snapshot import KpiSnapshot
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.info["test_engine"] = engine
    return session


def close_session(db: Session) -> None:
    engine = db.info["test_engine"]
    db.close()
    engine.dispose()


def create_department(db: Session, name: str) -> Department:
    department = Department(name=name)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def create_user(
    db: Session,
    department: Department,
    email: str,
    role: UserRole,
    *,
    password: str = "Password@123",
    is_active: bool = True,
) -> User:
    user = User(
        full_name=email.split("@")[0].title(),
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        department_id=department.id,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_task(
    db: Session,
    creator: User,
    assignee: User,
    *,
    title: str,
    status: TaskStatus,
    deadline=None,
    done_at=None,
    base_weight: int = 1,
    project_id: int | None = None,
    reopen_count: int = 0,
    estimated_hours: float | None = None,
) -> Task:
    task = Task(
        title=title,
        status=status,
        deadline=deadline,
        done_at=done_at,
        base_weight=base_weight,
        creator_id=creator.id,
        assignee_id=assignee.id,
        department_id=assignee.department_id,
        project_id=project_id,
        reopen_count=reopen_count,
        estimated_hours=estimated_hours,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def create_snapshot(db: Session, user: User, score: float, tasks_completed: int = 0) -> KpiSnapshot:
    now = datetime.now(timezone.utc)
    snapshot = KpiSnapshot(
        user_id=user.id,
        period_type="MONTHLY",
        period_key=f"{now.year}-{now.month:02d}",
        total_score=score,
        tasks_completed=tasks_completed,
        tasks_overdue=0,
        breakdown={},
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_activity(db: Session, user: User, description: str) -> ActivityLog:
    activity = ActivityLog(
        user_id=user.id,
        action_type="UPDATE",
        entity_type="TASK",
        entity_id=1,
        description=description,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity
