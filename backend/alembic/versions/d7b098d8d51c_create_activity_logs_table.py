# """create_activity_logs_table"""

# revision = 'd7b098d8d51c'
# down_revision = '0742ff57fe48'
# branch_labels = None
# depends_on = None

# from alembic import op
# import sqlalchemy as sa


# def upgrade() -> None:
#     op.create_table(
#         'activity_logs',
#         sa.Column('id', sa.Integer(), nullable=False),
#         sa.Column('action', sa.String(length=50), nullable=False),
#         sa.Column('description', sa.String(length=255), nullable=False),
#         sa.Column(
#             'user_id',
#             sa.Integer(),
#             sa.ForeignKey('users.id', ondelete='SET NULL'),
#             nullable=True,
#         ),
#         sa.Column(
#             'created_at',
#             sa.DateTime(timezone=True),
#             server_default=sa.text('now()'),
#             nullable=True,
#         ),
#         sa.PrimaryKeyConstraint('id'),
#     )
#     op.create_index(
#         op.f('ix_activity_logs_id'),
#         'activity_logs',
#         ['id'],
#         unique=False,
#     )


# def downgrade() -> None:
#     op.drop_index(op.f('ix_activity_logs_id'), table_name='activity_logs')
#     op.drop_table('activity_logs')

"""create_activity_logs_table"""

revision = 'd7b098d8d51c'
down_revision = '0742ff57fe48'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # activity_logs table already created in previous migration
    pass


def downgrade() -> None:
    pass