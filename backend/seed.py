from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.kpi_rule import KpiRule
from app.models.project import (
    Project,
    ProjectMember,
    ProjectMemberRole,
    ProjectPriority,
    ProjectStatus,
    ProjectStatusHistory,
)
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.services.kpi_engine import KpiEngine
from app.services.project_progress_engine import ProjectProgressEngine

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


def seed_projects(db: Session, departments: list[Department], users: list[User]) -> dict[str, Project]:
    department_map = {department.name: department.id for department in departments}
    user_map = {user.email: user for user in users}
    today = date.today()
    project_specs = [
        {
            "code": "ENG-PLATFORM",
            "name": "Engineering Platform Stabilization",
            "description": "Stabilize backend services, authorization, and delivery automation.",
            "department": "Engineering",
            "manager": "binh@company.local",
            "priority": ProjectPriority.HIGH,
            "project_weight": 1.2,
            "estimated_hours": 96,
            "members": {
                "cuc@company.local": 50,
                "duy@company.local": 50,
            },
        },
        {
            "code": "ENG-KPI",
            "name": "KPI Dashboard Reliability",
            "description": "Improve KPI reporting, notifications, and dashboard verification.",
            "department": "Engineering",
            "manager": "binh@company.local",
            "priority": ProjectPriority.MEDIUM,
            "project_weight": 1.0,
            "estimated_hours": 56,
            "members": {
                "chau@company.local": 100,
            },
        },
        {
            "code": "BIZ-KPI",
            "name": "Business KPI Rollout",
            "description": "Prepare KPI policies, reports, and communication for business teams.",
            "department": "Business Operations",
            "manager": "dao@company.local",
            "priority": ProjectPriority.HIGH,
            "project_weight": 1.1,
            "estimated_hours": 72,
            "members": {
                "em@company.local": 50,
                "ha@company.local": 50,
            },
        },
        {
            "code": "BIZ-OPS",
            "name": "Operations Data Quality",
            "description": "Clean operational data and align incentive calculation inputs.",
            "department": "Business Operations",
            "manager": "dao@company.local",
            "priority": ProjectPriority.MEDIUM,
            "project_weight": 1.0,
            "estimated_hours": 64,
            "members": {
                "giang@company.local": 50,
                "linh@company.local": 50,
            },
        },
    ]

    projects: dict[str, Project] = {}
    for spec in project_specs:
        manager = user_map[spec["manager"]]
        project = db.query(Project).filter(Project.code == spec["code"]).first()
        is_new = project is None
        if project is None:
            project = Project(code=spec["code"], created_by=manager.id)
        project.name = spec["name"]
        project.description = spec["description"]
        project.status = ProjectStatus.ACTIVE.value
        project.priority = spec["priority"]
        project.department_id = department_map[spec["department"]]
        project.manager_id = manager.id
        project.start_date = today - timedelta(days=7)
        project.end_date = today + timedelta(days=30)
        project.estimated_hours = spec["estimated_hours"]
        project.project_weight = spec["project_weight"]
        project.updated_by = manager.id
        if is_new:
            db.add(project)
            db.flush()
            db.add(ProjectStatusHistory(
                project_id=project.id,
                from_status=None,
                to_status=ProjectStatus.ACTIVE.value,
                changed_by=manager.id,
                reason="Created by demo seed",
            ))
        projects[spec["code"]] = project

        memberships = {
            spec["manager"]: (ProjectMemberRole.PROJECT_MANAGER, 0),
            **{
                email: (ProjectMemberRole.MEMBER, contribution_share)
                for email, contribution_share in spec["members"].items()
            },
        }
        for email, (role, contribution_share) in memberships.items():
            user = user_map[email]
            member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
            ).first()
            if member is None:
                member = ProjectMember(project_id=project.id, user_id=user.id)
                db.add(member)
            member.role = role
            member.contribution_share = contribution_share
            member.is_active = True
            member.added_by = manager.id

    db.commit()
    return projects


def seed_tasks(db: Session, departments: list[Department], users: list[User],
               projects: dict[str, Project]) -> None:
    department_map = {department.name: department.id for department in departments}
    user_map = {user.email: user for user in users}
    today = date.today()
    now = datetime.now(UTC).replace(tzinfo=None)

    db.query(Task).delete(synchronize_session=False)

    task_specs = [
        ("Implement refresh token flow", "Add secure token renewal for authenticated sessions.", TaskStatus.DOING, 4, 4, "binh@company.local", "cuc@company.local", "ENG-PLATFORM", 14, 6, 0, None),
        ("Review access control matrix", "Verify admin, manager, and staff permission boundaries.", TaskStatus.DONE, -2, 3, "binh@company.local", "cuc@company.local", "ENG-PLATFORM", 8, 8, 0, -3),
        ("Add project task filters", "Support project-aware task filters in manager workflows.", TaskStatus.TODO, 6, 3, "binh@company.local", "duy@company.local", "ENG-PLATFORM", 10, 0, 0, None),
        ("Optimize dashboard aggregate queries", "Reduce repeated queries in dashboard endpoints.", TaskStatus.BLOCKED, 1, 5, "binh@company.local", "duy@company.local", "ENG-PLATFORM", 16, 4, 0, None),
        ("Write notification integration tests", "Cover scheduler and notification delivery behavior.", TaskStatus.IN_REVIEW, 2, 4, "binh@company.local", "chau@company.local", "ENG-KPI", 12, 10, 0, None),
        ("Fix notification JSON accessor", "Use SQLAlchemy 2 JSON accessors for deduplication.", TaskStatus.DONE, -3, 3, "binh@company.local", "chau@company.local", "ENG-KPI", 6, 6, 0, -2),
        ("Prepare KPI policy guide", "Document the monthly KPI rules for business teams.", TaskStatus.DOING, 5, 3, "dao@company.local", "em@company.local", "BIZ-KPI", 10, 5, 0, None),
        ("Validate monthly KPI report", "Check report figures against approved KPI rules.", TaskStatus.DONE, -1, 4, "dao@company.local", "em@company.local", "BIZ-KPI", 8, 8, 0, -2),
        ("Clean CRM contact mapping", "Normalize duplicate and incomplete CRM contact records.", TaskStatus.TODO, 7, 2, "dao@company.local", "giang@company.local", "BIZ-OPS", 12, 0, 0, None),
        ("Draft sales KPI checklist", "Prepare the review checklist for monthly sales KPI input.", TaskStatus.IN_REVIEW, 3, 3, "dao@company.local", "giang@company.local", "BIZ-OPS", 8, 7, 0, None),
        ("Backfill business KPI baseline", "Collect missing KPI baseline values for the current quarter.", TaskStatus.BLOCKED, -1, 5, "dao@company.local", "ha@company.local", "BIZ-KPI", 14, 6, 0, None),
        ("Review notification content", "Review KPI alert wording before business rollout.", TaskStatus.DONE, -4, 2, "dao@company.local", "ha@company.local", "BIZ-KPI", 5, 5, 0, -4),
        ("Prepare onboarding KPI FAQ", "Create an FAQ for new employees using the KPI system.", TaskStatus.TODO, 8, 2, "dao@company.local", "linh@company.local", "BIZ-OPS", 7, 0, 0, None),
        ("Audit incentive calculation inputs", "Verify source fields used by the incentive calculation.", TaskStatus.DONE, -5, 4, "dao@company.local", "linh@company.local", "BIZ-OPS", 9, 9, 1, -3),
    ]

    for (
        title, description, task_status, deadline_offset, base_weight,
        creator_email, assignee_email, project_code, estimated_hours,
        actual_hours, reopen_count, done_offset,
    ) in task_specs:
        creator = user_map[creator_email]
        assignee = user_map[assignee_email]
        project = projects[project_code]
        task = Task(
            title=title,
            description=description,
            status=task_status,
            deadline=today + timedelta(days=deadline_offset),
            done_at=now + timedelta(days=done_offset) if done_offset is not None else None,
            base_weight=base_weight,
            creator_id=creator.id,
            assignee_id=assignee.id,
            reviewer_id=project.manager_id,
            department_id=department_map[
                "Engineering" if project_code.startswith("ENG-") else "Business Operations"
            ],
            project_id=project.id,
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
            reopen_count=reopen_count,
        )
        db.add(task)

    db.commit()


def recalculate_seed_project_progress(db: Session, projects: dict[str, Project]) -> None:
    engine = ProjectProgressEngine(db)
    for project in projects.values():
        engine.calculate(project)


def seed_kpi_rules(db: Session) -> None:
    rules = [
        ("BASE_COMPLETION", "Base score multiplier for completed task weight", 1.0),
        ("ON_TIME_BONUS", "Multiplier for tasks completed on or before deadline", 1.2),
        ("OVERDUE_PENALTY", "Multiplier for completed tasks finished after deadline", 0.5),
        ("REOPEN_PENALTY", "Flat penalty per task reopen", -5.0),
    ]
    for code, description, multiplier in rules:
        rule = db.query(KpiRule).filter(KpiRule.code == code).first()
        if rule is None:
            db.add(KpiRule(code=code, description=description, multiplier=multiplier, is_active=True))
        else:
            rule.description = description
            rule.multiplier = multiplier
            rule.is_active = True
    db.commit()


def recalculate_seed_kpis(db: Session, users: list[User]) -> None:
    engine = KpiEngine(db)
    for user in users:
        if user.is_active:
            engine.recalculate_monthly_kpi(user.id)


def main() -> None:
    db = SessionLocal()
    try:
        departments = seed_departments(db)
        users = seed_users(db, departments)
        projects = seed_projects(db, departments, users)
        seed_tasks(db, departments, users, projects)
        seed_kpi_rules(db)
        recalculate_seed_kpis(db, users)
        recalculate_seed_project_progress(db, projects)
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
