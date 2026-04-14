"""create core tables"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260331_003700"
down_revision = None
branch_labels = None
depends_on = None


task_status = postgresql.ENUM("todo", "doing", "done", name="task_status", create_type=False)


def upgrade() -> None:
    task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            task_status,
            nullable=False,
            server_default="todo",
        ),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("done_at", sa.DateTime(), nullable=True),
        sa.Column("base_weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
    )

    op.create_index("ix_departments_id", "departments", ["id"], unique=False)
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)
    op.create_index("ix_tasks_deadline", "tasks", ["deadline"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_deadline", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_id", table_name="tasks")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_departments_id", table_name="departments")
    op.drop_table("tasks")
    op.drop_table("users")
    op.drop_table("departments")
    task_status.drop(op.get_bind(), checkfirst=True)
