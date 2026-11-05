"""employee max weekly hours

Revision ID: 3a7c9e1f2b40
Revises: 89510c048e94
Create Date: 2026-11-05 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3a7c9e1f2b40"
down_revision: str | None = "89510c048e94"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("max_weekly_hours", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "max_weekly_hours")
