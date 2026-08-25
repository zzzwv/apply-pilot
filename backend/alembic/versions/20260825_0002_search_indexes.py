"""Add trigram indexes for application searching."""

from alembic import op

revision = "20260825_0002"
down_revision = "20260824_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_companies_full_name_trgm ON companies USING gin "
        "(full_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_companies_short_name_trgm ON companies USING gin "
        "(short_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_companies_industry_trgm ON companies USING gin "
        "(industry gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_job_applications_job_title_trgm ON job_applications USING gin "
        "(job_title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_job_applications_note_trgm ON job_applications USING gin "
        "(note gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_job_applications_note_trgm")
    op.execute("DROP INDEX IF EXISTS ix_job_applications_job_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_companies_industry_trgm")
    op.execute("DROP INDEX IF EXISTS ix_companies_short_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_companies_full_name_trgm")
