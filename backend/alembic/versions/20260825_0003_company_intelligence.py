"""Add recruitment-link verification and source provenance."""

import sqlalchemy as sa

from alembic import op

revision = "20260825_0003"
down_revision = "20260825_0002"
branch_labels = None
depends_on = None


verification_status = sa.Enum(
    "unverified",
    "candidate",
    "verified",
    "rejected",
    name="verificationstatus",
)


def add_column_if_missing(existing_columns: set[str], column: sa.Column[object]) -> bool:
    if column.name in existing_columns:
        return False

    op.add_column("recruitment_links", column)
    existing_columns.add(column.name)
    return True


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {
        column["name"] for column in sa.inspect(bind).get_columns("recruitment_links")
    }
    verification_status.create(bind, checkfirst=True)
    added_verification_status = add_column_if_missing(
        existing_columns,
        sa.Column(
            "verification_status",
            verification_status,
            nullable=False,
            server_default=sa.text("'unverified'"),
        ),
    )
    if added_verification_status:
        op.alter_column("recruitment_links", "verification_status", server_default=None)
    add_column_if_missing(
        existing_columns, sa.Column("http_status", sa.Integer(), nullable=True)
    )
    add_column_if_missing(
        existing_columns, sa.Column("final_url", sa.String(length=2048), nullable=True)
    )
    add_column_if_missing(
        existing_columns, sa.Column("source_url", sa.String(length=2048), nullable=True)
    )
    add_column_if_missing(
        existing_columns, sa.Column("source_title", sa.String(length=512), nullable=True)
    )
    add_column_if_missing(
        existing_columns, sa.Column("source_type", sa.String(length=64), nullable=True)
    )
    add_column_if_missing(
        existing_columns,
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recruitment_links", "retrieved_at")
    op.drop_column("recruitment_links", "source_type")
    op.drop_column("recruitment_links", "source_title")
    op.drop_column("recruitment_links", "source_url")
    op.drop_column("recruitment_links", "final_url")
    op.drop_column("recruitment_links", "http_status")
    op.drop_column("recruitment_links", "verification_status")
    verification_status.drop(op.get_bind(), checkfirst=True)
