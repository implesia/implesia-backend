"""team member portrait

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("team_members", sa.Column("image_url", sa.String(length=255), nullable=True))
    op.create_table(
        "team_images",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("team_images")
    op.drop_column("team_members", "image_url")
