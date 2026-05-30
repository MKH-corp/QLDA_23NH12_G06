"""Add metadata fields to notifications for rule-based alerts

This migration adds severity, source, metadata_json, and is_ai_generated columns
to support the NotificationEngine for rule-based alerts.
"""

revision = '20260530_001'
down_revision = '20260510_000001'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('notifications', sa.Column('severity', sa.String(50), nullable=False, server_default='info'))
    op.add_column('notifications', sa.Column('source', sa.String(50), nullable=False, server_default='system'))
    op.add_column('notifications', sa.Column('metadata_json', sa.JSON(), nullable=True))
    op.add_column('notifications', sa.Column('is_ai_generated', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('notifications', 'is_ai_generated')
    op.drop_column('notifications', 'metadata_json')
    op.drop_column('notifications', 'source')
    op.drop_column('notifications', 'severity')
