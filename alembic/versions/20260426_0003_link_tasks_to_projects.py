"""link tasks to projects with project_id

Revision ID: 20260426_0003
Revises: 20260426_0002
Create Date: 2026-04-26 19:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260426_0003"
down_revision = "20260426_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_tasks", sa.Column("project_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_document_tasks_project_id"), "document_tasks", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_tasks_project_id"), table_name="document_tasks")
    op.drop_column("document_tasks", "project_id")
