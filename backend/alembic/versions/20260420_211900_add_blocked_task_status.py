"""add blocked task status"""

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260420_211900"
down_revision = "20260331_003700"
branch_labels = None
depends_on = None

old_task_status = postgresql.ENUM("todo", "doing", "done", name="task_status", create_type=False)
new_task_status = postgresql.ENUM("todo", "doing", "blocked", "done", name="task_status", create_type=False)


def upgrade() -> None:
    op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'blocked'")


def downgrade() -> None:
    bind = op.get_bind()
    new_task_status.drop(bind, checkfirst=False)
    old_task_status.create(bind, checkfirst=False)
    op.execute(
        "ALTER TABLE tasks ALTER COLUMN status TYPE task_status USING "
        "CASE WHEN status::text = 'blocked' THEN 'doing'::task_status ELSE status::text::task_status END"
    )
