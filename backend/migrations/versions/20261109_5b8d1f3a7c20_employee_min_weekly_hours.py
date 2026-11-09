"""employee min weekly hours

Revision ID: 5b8d1f3a7c20
Revises: 6d2e4f8a9b10
Create Date: 2026-11-09 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5b8d1f3a7c20"
down_revision: str | None = "6d2e4f8a9b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("min_weekly_hours", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "min_weekly_hours")
