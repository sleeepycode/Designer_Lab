"""initial document_tasks table

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26 18:50:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260426_0001"
down_revision = None
branch_labels = None
depends_on = None


task_status_enum = sa.Enum("created", "completed", "failed", name="task_status")


def upgrade() -> None:
    bind = op.get_bind()
    task_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "document_tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("status", task_status_enum, nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("input_path", sa.String(), nullable=False),
        sa.Column("output_path", sa.String(), nullable=True),
        sa.Column("report_path", sa.String(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_tasks_user_id"), "document_tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_tasks_user_id"), table_name="document_tasks")
    op.drop_table("document_tasks")
    bind = op.get_bind()
    task_status_enum.drop(bind, checkfirst=True)
