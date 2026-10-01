"""create meetings table

Revision ID: 0001
Revises:
Create Date: 2026-09-30
"""
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attendee_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_meetings_starts_at", "meetings", ["starts_at"])


def downgrade() -> None:
    op.drop_index("ix_meetings_starts_at", table_name="meetings")
    op.drop_table("meetings")
