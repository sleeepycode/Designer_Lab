"""unify project statuses lifecycle

Revision ID: 20260426_0004
Revises: 20260426_0003
Create Date: 2026-04-26 21:10:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260426_0004"
down_revision = "20260426_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create new enum with unified lifecycle statuses.
    op.execute("CREATE TYPE project_status_v2 AS ENUM ('uploaded', 'processing', 'analyzing', 'ready', 'error')")
    # Map legacy `created` to `uploaded` while converting type.
    op.execute(
        """
        ALTER TABLE projects
        ALTER COLUMN status TYPE project_status_v2
        USING (
            CASE
                WHEN status::text = 'created' THEN 'uploaded'::project_status_v2
                ELSE status::text::project_status_v2
            END
        )
        """
    )
    op.execute("DROP TYPE project_status")
    op.execute("ALTER TYPE project_status_v2 RENAME TO project_status")


def downgrade() -> None:
    op.execute("CREATE TYPE project_status_v1 AS ENUM ('created', 'uploaded', 'processing', 'ready', 'error')")
    # Map `analyzing` back to `processing` during rollback.
    op.execute(
        """
        ALTER TABLE projects
        ALTER COLUMN status TYPE project_status_v1
        USING (
            CASE
                WHEN status::text = 'analyzing' THEN 'processing'::project_status_v1
                ELSE status::text::project_status_v1
            END
        )
        """
    )
    op.execute("DROP TYPE project_status")
    op.execute("ALTER TYPE project_status_v1 RENAME TO project_status")
