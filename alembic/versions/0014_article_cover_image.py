"""article cover image

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("image_url", sa.String(length=255), nullable=True))
    op.create_table(
        "article_images",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("article_images")
    op.drop_column("articles", "image_url")
