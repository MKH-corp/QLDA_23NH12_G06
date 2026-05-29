"""Enterprise Project Management System - Full Schema

Lý do tạo các bảng/cột mới:
- projects: thêm code, manager_id, priority, progress_percentage,
  estimated/actual_hours, budget, created_by, updated_by, archived_at, timestamps
  → hỗ trợ lifecycle rõ ràng, audit, analytics
- project_members: quản lý thành viên và phân quyền trong project
  → tách khỏi department để project cross-department được
- project_status_history: lưu mọi lần đổi status với lý do
  → audit trail bắt buộc cho enterprise
- project_milestones: theo dõi mốc tiến độ
  → cơ sở tính KPI bonus và progress engine
- project_audit_logs: ghi field-level changes (trước/sau)
  → ai đổi gì, lúc nào, từ giá trị nào sang giá trị nào

Backward compatible: KHÔNG xóa cột/bảng cũ.
"""

revision = '20260510_000001'
down_revision = 'af4b79318645'   # kế tiếp sau create_kpi_tables
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ── Enum types ─────────────────────────────────────────────────────────────
project_priority_enum = postgresql.ENUM(
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
    name='project_priority', create_type=False
)
project_member_role_enum = postgresql.ENUM(
    'PROJECT_MANAGER', 'TEAM_LEAD', 'MEMBER', 'VIEWER',
    name='project_member_role', create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()

    # ── Tạo enum types ─────────────────────────────────────────────────
    project_priority_enum.create(bind, checkfirst=True)
    project_member_role_enum.create(bind, checkfirst=True)

    # ── Mở rộng bảng projects hiện có ──────────────────────────────────
    # Dùng checkfirst-style: thêm từng cột, không drop cột cũ
    op.add_column('projects', sa.Column('code', sa.String(50), nullable=True))
    op.add_column('projects', sa.Column(
        'manager_id', sa.Integer(),
        sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    ))
    op.add_column('projects', sa.Column(
        'priority', project_priority_enum,
        nullable=False, server_default='MEDIUM'
    ))
    op.add_column('projects', sa.Column(
        'progress_percentage', sa.Float(),
        nullable=False, server_default='0'
    ))
    op.add_column('projects', sa.Column('estimated_hours', sa.Float(), nullable=True))
    op.add_column('projects', sa.Column(
        'actual_hours', sa.Float(), nullable=False, server_default='0'
    ))
    op.add_column('projects', sa.Column('estimated_budget', sa.Float(), nullable=True))
    op.add_column('projects', sa.Column(
        'created_by', sa.Integer(),
        sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    ))
    op.add_column('projects', sa.Column(
        'updated_by', sa.Integer(),
        sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    ))
    op.add_column('projects', sa.Column(
        'archived_at', sa.DateTime(timezone=True), nullable=True
    ))
    op.add_column('projects', sa.Column(
        'created_at', sa.DateTime(timezone=True),
        server_default=sa.text('now()'), nullable=True
    ))
    op.add_column('projects', sa.Column(
        'updated_at', sa.DateTime(timezone=True),
        server_default=sa.text('now()'), nullable=True
    ))

    # Đổi cột status từ String sang String nhưng giữ nguyên data
    # (Không dùng ENUM để tránh migration conflict với cột cũ)
    # Cột status giữ nguyên kiểu String(50), validate ở service layer

    # ── Bảng project_members ───────────────────────────────────────────
    # Lý do: project có thể gồm thành viên cross-department,
    # cần phân quyền riêng trong project (không phải system role)
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', project_member_role_enum,
                  nullable=False, server_default='MEMBER'),
        sa.Column('joined_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('added_by', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )
    op.create_index('ix_project_members_project_id', 'project_members', ['project_id'])
    op.create_index('ix_project_members_user_id', 'project_members', ['user_id'])

    # ── Bảng project_status_history ────────────────────────────────────
    # Lý do: mọi thay đổi status phải có audit trail + lý do
    # để validate transition hợp lệ và báo cáo timeline
    op.create_table(
        'project_status_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(50), nullable=True),
        sa.Column('to_status', sa.String(50), nullable=False),
        sa.Column('changed_by', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_psh_project_id', 'project_status_history', ['project_id'])

    # ── Bảng project_milestones ────────────────────────────────────────
    # Lý do: milestone completion = cơ sở tính KPI bonus,
    # progress engine, và risk indicator
    op.create_table(
        'project_milestones',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(),
                  nullable=False, server_default='false'),
        sa.Column('weight', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_milestones_project_id', 'project_milestones', ['project_id'])

    # ── Bảng project_audit_logs ────────────────────────────────────────
    # Lý do: field-level audit — ghi trước/sau từng thay đổi
    # để trả lời "ai đổi gì, khi nào, từ giá trị nào sang giá trị nào"
    op.create_table(
        'project_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('changed_by', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_pal_project_id', 'project_audit_logs', ['project_id'])
    op.create_index('ix_pal_changed_by', 'project_audit_logs', ['changed_by'])


def downgrade() -> None:
    op.drop_table('project_audit_logs')
    op.drop_table('project_milestones')
    op.drop_table('project_status_history')
    op.drop_table('project_members')

    for col in [
        'updated_at', 'created_at', 'archived_at', 'updated_by', 'created_by',
        'estimated_budget', 'actual_hours', 'estimated_hours',
        'progress_percentage', 'priority', 'manager_id', 'code',
    ]:
        op.drop_column('projects', col)

    bind = op.get_bind()
    project_member_role_enum.drop(bind, checkfirst=True)
    project_priority_enum.drop(bind, checkfirst=True)