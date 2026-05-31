import unittest

from app.models.project import Project, ProjectMember, ProjectStatusHistory
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from seed import (
    recalculate_seed_kpis,
    recalculate_seed_project_progress,
    seed_departments,
    seed_kpi_rules,
    seed_projects,
    seed_tasks,
    seed_users,
)
from tests.helpers import close_session, make_session


class SeedDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()

    def tearDown(self) -> None:
        close_session(self.db)

    def test_seed_creates_balanced_project_tasks_and_is_repeatable(self) -> None:
        departments, users, projects = self._seed_all()

        self.assertEqual(self.db.query(Project).count(), 4)
        self.assertEqual(self.db.query(ProjectStatusHistory).count(), 4)
        self.assertEqual(self.db.query(Task).count(), 14)
        self._assert_balanced_staff_tasks()
        self._assert_tasks_have_active_project_memberships()

        manager = next(user for user in users if user.email == "binh@company.local")
        staff = next(user for user in users if user.email == "cuc@company.local")
        self.db.add(Task(
            title="Temporary task that should be reset",
            status=TaskStatus.TODO,
            creator_id=manager.id,
            assignee_id=staff.id,
            department_id=staff.department_id,
        ))
        self.db.commit()

        projects = seed_projects(self.db, departments, users)
        seed_tasks(self.db, departments, users, projects)
        recalculate_seed_project_progress(self.db, projects)

        self.assertEqual(self.db.query(Project).count(), 4)
        self.assertEqual(self.db.query(ProjectStatusHistory).count(), 4)
        self.assertEqual(self.db.query(Task).count(), 14)
        self.assertIsNone(
            self.db.query(Task)
            .filter(Task.title == "Temporary task that should be reset")
            .first()
        )
        self._assert_balanced_staff_tasks()
        self._assert_tasks_have_active_project_memberships()

    def _seed_all(self):
        departments = seed_departments(self.db)
        users = seed_users(self.db, departments)
        projects = seed_projects(self.db, departments, users)
        seed_tasks(self.db, departments, users, projects)
        seed_kpi_rules(self.db)
        recalculate_seed_kpis(self.db, users)
        recalculate_seed_project_progress(self.db, projects)
        return departments, users, projects

    def _assert_balanced_staff_tasks(self) -> None:
        staff_users = self.db.query(User).filter(User.role == UserRole.STAFF).all()
        self.assertEqual(len(staff_users), 7)
        for staff in staff_users:
            self.assertEqual(
                self.db.query(Task).filter(Task.assignee_id == staff.id).count(),
                2,
                staff.email,
            )

    def _assert_tasks_have_active_project_memberships(self) -> None:
        for task in self.db.query(Task).all():
            self.assertIsNotNone(task.project_id, task.title)
            self.assertIsNotNone(task.reviewer_id, task.title)
            membership = (
                self.db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == task.project_id,
                    ProjectMember.user_id == task.assignee_id,
                    ProjectMember.is_active == True,
                )
                .first()
            )
            self.assertIsNotNone(membership, task.title)


if __name__ == "__main__":
    unittest.main()
