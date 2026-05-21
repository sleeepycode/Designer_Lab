"""add user display_name

Revision ID: 20260520_0006
Revises: 20260520_0005
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa

revision = "20260520_0006"
down_revision = "20260520_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "display_name")
