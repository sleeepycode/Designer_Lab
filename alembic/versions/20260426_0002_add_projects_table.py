"""add projects table

Revision ID: 20260426_0002
Revises: 20260426_0001
Create Date: 2026-04-26 19:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260426_0002"
down_revision = "20260426_0001"
branch_labels = None
depends_on = None


project_status_enum = sa.Enum("created", "uploaded", "processing", "ready", "error", name="project_status")


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("status", project_status_enum, nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("metadata_path", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
    bind = op.get_bind()
    project_status_enum.drop(bind, checkfirst=True)
