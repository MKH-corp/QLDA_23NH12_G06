from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole

DEFAULT_PASSWORD = "Password@123"


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
    existing_users = db.query(User).order_by(User.id).all()
    default_password_hash = get_password_hash(DEFAULT_PASSWORD)

    if existing_users:
        changed = False
        role_map = {
            "an@company.local": UserRole.ADMIN,
            "binh@company.local": UserRole.MANAGER,
            "dao@company.local": UserRole.MANAGER,
        }
        for user in existing_users:
            if not user.password_hash:
                user.password_hash = default_password_hash
                changed = True
            if not user.role:
                user.role = role_map.get(user.email, UserRole.STAFF)
                changed = True
            if user.is_active is None:
                user.is_active = True
                changed = True
        if changed:
            db.commit()
        return db.query(User).order_by(User.id).all()

    engineering_id = departments[0].id
    business_id = departments[1].id

    users = [
        User(full_name="Nguyen Van An", email="an@company.local", password_hash=default_password_hash, role=UserRole.ADMIN, department_id=engineering_id, is_active=True),
        User(full_name="Tran Minh Binh", email="binh@company.local", password_hash=default_password_hash, role=UserRole.MANAGER, department_id=engineering_id, is_active=True),
        User(full_name="Le Thu Cuc", email="cuc@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=engineering_id, is_active=True),
        User(full_name="Pham Gia Duy", email="duy@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=engineering_id, is_active=True),
        User(full_name="Hoang Bao Chau", email="chau@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=engineering_id, is_active=True),
        User(full_name="Vo Quynh Dao", email="dao@company.local", password_hash=default_password_hash, role=UserRole.MANAGER, department_id=business_id, is_active=True),
        User(full_name="Bui Khac Em", email="em@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=business_id, is_active=True),
        User(full_name="Dang Thanh Giang", email="giang@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=business_id, is_active=True),
        User(full_name="Ly Hong Ha", email="ha@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=business_id, is_active=True),
        User(full_name="Do Khanh Linh", email="linh@company.local", password_hash=default_password_hash, role=UserRole.STAFF, department_id=business_id, is_active=True),
    ]
    db.add_all(users)
    db.commit()
    return db.query(User).order_by(User.id).all()


def seed_tasks(db: Session, departments: list[Department], users: list[User]) -> None:
    if db.query(Task).count():
        return

    department_map = {department.name: department.id for department in departments}
    user_map = {user.email: user for user in users}

    tasks = [
        Task(
            title="Setup CI pipeline",
            description="Prepare CI for backend service",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=3),
            base_weight=3,
            creator_id=user_map["an@company.local"].id,
            assignee_id=user_map["binh@company.local"].id,
            department_id=department_map["Engineering"],
        ),
        Task(
            title="Finalize auth middleware",
            description="Review JWT middleware and secure protected routes",
            status=TaskStatus.BLOCKED,
            deadline=date.today() + timedelta(days=2),
            base_weight=4,
            creator_id=user_map["binh@company.local"].id,
            assignee_id=user_map["cuc@company.local"].id,
            department_id=department_map["Engineering"],
        ),
        Task(
            title="Refactor task service",
            description="Split validation and permission checks for Sprint 2",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=5),
            base_weight=3,
            creator_id=user_map["binh@company.local"].id,
            assignee_id=user_map["duy@company.local"].id,
            department_id=department_map["Engineering"],
        ),
        Task(
            title="Fix overdue query regression",
            description="Correct task listing for overdue dashboard widgets",
            status=TaskStatus.DONE,
            deadline=date.today() - timedelta(days=1),
            done_at=None,
            base_weight=2,
            creator_id=user_map["an@company.local"].id,
            assignee_id=user_map["chau@company.local"].id,
            department_id=department_map["Engineering"],
        ),
        Task(
            title="Prepare quarterly KPI deck",
            description="Draft KPI slides for board review",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=4),
            base_weight=3,
            creator_id=user_map["dao@company.local"].id,
            assignee_id=user_map["em@company.local"].id,
            department_id=department_map["Business Operations"],
        ),
        Task(
            title="Clean CRM duplicates",
            description="Merge duplicate accounts before KPI export",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=6),
            base_weight=1,
            creator_id=user_map["dao@company.local"].id,
            assignee_id=user_map["giang@company.local"].id,
            department_id=department_map["Business Operations"],
        ),
        Task(
            title="Backfill KPI baseline data",
            description="Collect missing KPI baseline metrics for Q2",
            status=TaskStatus.BLOCKED,
            deadline=date.today() + timedelta(days=1),
            base_weight=5,
            creator_id=user_map["dao@company.local"].id,
            assignee_id=user_map["ha@company.local"].id,
            department_id=department_map["Business Operations"],
        ),
        Task(
            title="Review sales incentive policy",
            description="Align incentive draft with KPI definitions",
            status=TaskStatus.DONE,
            deadline=date.today() - timedelta(days=3),
            done_at=None,
            base_weight=2,
            creator_id=user_map["dao@company.local"].id,
            assignee_id=user_map["linh@company.local"].id,
            department_id=department_map["Business Operations"],
        ),
        Task(
            title="Prepare sprint retrospective",
            description="Summarize wins, blockers, and next actions",
            status=TaskStatus.DOING,
            deadline=date.today() + timedelta(days=1),
            base_weight=2,
            creator_id=user_map["an@company.local"].id,
            assignee_id=user_map["cuc@company.local"].id,
            department_id=department_map["Engineering"],
        ),
        Task(
            title="Update onboarding checklist",
            description="Reflect recent process changes in onboarding docs",
            status=TaskStatus.TODO,
            deadline=date.today() + timedelta(days=8),
            base_weight=1,
            creator_id=user_map["dao@company.local"].id,
            assignee_id=user_map["em@company.local"].id,
            department_id=department_map["Business Operations"],
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
        print("Test accounts:")
        print(f"- Admin: an@company.local / {DEFAULT_PASSWORD}")
        print(f"- Manager (Engineering): binh@company.local / {DEFAULT_PASSWORD}")
        print(f"- Manager (Business): dao@company.local / {DEFAULT_PASSWORD}")
        print(f"- Staff (Engineering): cuc@company.local / {DEFAULT_PASSWORD}")
        print(f"- Staff (Business): em@company.local / {DEFAULT_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
