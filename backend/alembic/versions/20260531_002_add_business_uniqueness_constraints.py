"""add business uniqueness constraints for KPI snapshots and projects"""

revision = "20260531_002"
down_revision = "20260531_001"
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM kpi_snapshots a
        USING kpi_snapshots b
        WHERE a.user_id = b.user_id
          AND a.period_type = b.period_type
          AND a.period_key = b.period_key
          AND a.id < b.id
        """
    )
    op.execute(
        """
        DELETE FROM kpi_records a
        USING kpi_records b
        WHERE a.user_id = b.user_id
          AND a.month = b.month
          AND a.year = b.year
          AND a.id < b.id
        """
    )
    op.execute(
        """
        UPDATE projects p
        SET code = p.code || '-' || p.id
        WHERE p.code IS NOT NULL
          AND p.id NOT IN (
            SELECT MIN(id)
            FROM projects
            WHERE code IS NOT NULL
            GROUP BY code
          )
        """
    )
    op.create_unique_constraint(
        "uq_kpi_snapshot_user_period",
        "kpi_snapshots",
        ["user_id", "period_type", "period_key"],
    )
    op.create_unique_constraint(
        "uq_kpi_record_user_month_year",
        "kpi_records",
        ["user_id", "month", "year"],
    )
    op.create_unique_constraint("uq_projects_code", "projects", ["code"])


def downgrade() -> None:
    op.drop_constraint("uq_projects_code", "projects", type_="unique")
    op.drop_constraint("uq_kpi_record_user_month_year", "kpi_records", type_="unique")
    op.drop_constraint("uq_kpi_snapshot_user_period", "kpi_snapshots", type_="unique")
