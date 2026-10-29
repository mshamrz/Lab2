"""add agenda and ai_suggestion columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("meetings", sa.Column("agenda", sa.JSON(), nullable=True))
    op.add_column("meetings", sa.Column("ai_suggestion", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("meetings", "ai_suggestion")
    op.drop_column("meetings", "agenda")
