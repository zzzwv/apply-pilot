"""Add idempotent client sync identity."""

import sqlalchemy as sa

from alembic import op

revision = "20260826_0004"
down_revision = "20260825_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("job_applications")}

    if "client_sync_id" not in column_names:
        op.add_column("job_applications", sa.Column("client_sync_id", sa.Uuid(), nullable=True))

    index_name = "uq_job_applications_user_client_sync_id"
    index_names = {index["name"] for index in inspector.get_indexes("job_applications")}
    if index_name not in index_names:
        op.create_index(
            index_name,
            "job_applications",
            ["user_id", "client_sync_id"],
            unique=True,
            postgresql_where=sa.text("client_sync_id IS NOT NULL"),
        )


def downgrade() -> None:
    op.drop_index("uq_job_applications_user_client_sync_id", table_name="job_applications")
    op.drop_column("job_applications", "client_sync_id")
