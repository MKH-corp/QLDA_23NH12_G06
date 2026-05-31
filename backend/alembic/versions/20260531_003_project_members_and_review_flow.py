"""add project membership controls and task review fields"""

revision = "20260531_003"
down_revision = "20260531_002"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.add_column("projects", sa.Column("project_weight", sa.Float(), nullable=False, server_default="1"))
    op.add_column("project_members", sa.Column("contribution_share", sa.Float(), nullable=False, server_default="0"))
    op.add_column("project_members", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    if dialect == "postgresql":
        op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'in_review'")

    op.add_column("tasks", sa.Column("reviewer_id", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("estimated_hours", sa.Float(), nullable=True))
    op.add_column("tasks", sa.Column("actual_hours", sa.Float(), nullable=False, server_default="0"))
    op.create_foreign_key("fk_tasks_reviewer_id_users", "tasks", "users", ["reviewer_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_tasks_reviewer_id_users", "tasks", type_="foreignkey")
    op.drop_column("tasks", "actual_hours")
    op.drop_column("tasks", "estimated_hours")
    op.drop_column("tasks", "reviewer_id")
    op.drop_column("project_members", "is_active")
    op.drop_column("project_members", "contribution_share")
    op.drop_column("projects", "project_weight")
