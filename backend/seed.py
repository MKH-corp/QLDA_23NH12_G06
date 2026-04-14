from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.department import Department
from app.models.task import Task, TaskStatus
from app.models.user import User


def seed_departments(db: Session) -> list[Department]:
    existing = db.query(Department).count()
    if existing:
        return db.query(Department).order_by(Department.id).all()

    departments = [
        Department(name="Engineering"),
        Department(name="Business Operations"),
    ]
    db.add_all(departments)
    db.commit()
    return db.query(Department).order_by(Department.id).all()


def seed_users(db: Session, departments: list[Department]) -> list[User]:
    existing = db.query(User).count()
    if existing:
        return db.query(User).order_by(User.id).all()

    engineering_id = departments[0].id
    business_id = departments[1].id

    users = [
        User(full_name="Nguyen Van An", email="an@company.local", department_id=engineering_id),
        User(full_name="Tran Minh Binh", email="binh@company.local", department_id=engineering_id),
        User(full_name="Le Thu Cuc", email="cuc@company.local", department_id=engineering_id),
        User(full_name="Pham Gia Duy", email="duy@company.local", department_id=engineering_id),
        User(full_name="Hoang Bao Chau", email="chau@company.local", department_id=engineering_id),
        User(full_name="Vo Quynh Dao", email="dao@company.local", department_id=business_id),
        User(full_name="Bui Khac Em", email="em@company.local", department_id=business_id),
        User(full_name="Dang Thanh Giang", email="giang@company.local", department_id=business_id),
        User(full_name="Ly Hong Ha", email="ha@company.local", department_id=business_id),
        User(full_name="Do Khanh Linh", email="linh@company.local", department_id=business_id),
    ]
    db.add_all(users)
    db.commit()
    return db.query(User).order_by(User.id).all()


def seed_tasks(db: Session, departments: list[Department], users: list[User]) -> None:
    if db.query(Task).count():
        return

    engineering_id = departments[0].id
    business_id = departments[1].id

    tasks = [
        Task(
            title="Setup CI pipeline",
            description="Prepare CI for backend service",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=3),
            base_weight=3,
            creator_id=users[0].id,
            assignee_id=users[1].id,
            department_id=engineering_id,
        ),
        Task(
            title="Design task schema",
            description="Finalize DB schema for task tracking",
            status=TaskStatus.DONE,
            deadline=date.today() - timedelta(days=2),
            done_at=None,
            base_weight=2,
            creator_id=users[1].id,
            assignee_id=users[2].id,
            department_id=engineering_id,
        ),
        Task(
            title="Refactor auth module",
            description="Improve auth service separation",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=7),
            base_weight=2,
            creator_id=users[2].id,
            assignee_id=users[3].id,
            department_id=engineering_id,
        ),
        Task(
            title="Optimize report query",
            description="Reduce report generation time",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=5),
            base_weight=5,
            creator_id=users[3].id,
            assignee_id=users[4].id,
            department_id=engineering_id,
        ),
        Task(
            title="Fix overdue notification bug",
            description="Notifications not sent for overdue tasks",
            status=TaskStatus.TODO,
            deadline=date.today() - timedelta(days=1),
            base_weight=4,
            creator_id=users[4].id,
            assignee_id=users[0].id,
            department_id=engineering_id,
        ),
        Task(
            title="Prepare quarterly KPI deck",
            description="Draft KPI presentation for board review",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=4),
            base_weight=3,
            creator_id=users[5].id,
            assignee_id=users[6].id,
            department_id=business_id,
        ),
        Task(
            title="Clean CRM duplicates",
            description="Merge duplicate company records",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=6),
            base_weight=1,
            creator_id=users[6].id,
            assignee_id=users[7].id,
            department_id=business_id,
        ),
        Task(
            title="Review sales incentive policy",
            description="Align policy with KPI framework",
            status=TaskStatus.DONE,
            deadline=date.today() - timedelta(days=4),
            done_at=None,
            base_weight=2,
            creator_id=users[7].id,
            assignee_id=users[8].id,
            department_id=business_id,
        ),
        Task(
            title="Backfill KPI baseline data",
            description="Collect missing KPI baseline metrics",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=2),
            base_weight=4,
            creator_id=users[8].id,
            assignee_id=users[9].id,
            department_id=business_id,
        ),
        Task(
            title="Update onboarding checklist",
            description="Reflect process changes in onboarding",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=8),
            base_weight=1,
            creator_id=users[9].id,
            assignee_id=users[5].id,
            department_id=business_id,
        ),
        Task(
            title="Prepare sprint retrospective",
            description="Summarize wins, blockers, and actions",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=1),
            base_weight=2,
            creator_id=users[0].id,
            assignee_id=users[2].id,
            department_id=engineering_id,
        ),
        Task(
            title="Create KPI glossary",
            description="Standardize KPI definitions across teams",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=9),
            base_weight=2,
            creator_id=users[5].id,
            assignee_id=users[8].id,
            department_id=business_id,
        ),
    ]

    for task in tasks:
        if task.status == TaskStatus.DONE:
            task.done_at = task.done_at or datetime.now(UTC).replace(tzinfo=None)

    db.add_all(tasks)
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        departments = seed_departments(db)
        users = seed_users(db, departments)
        seed_tasks(db, departments, users)
        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()