"""sales demand source and stored weekly load

Revision ID: 6d2e4f8a9b10
Revises: 3a7c9e1f2b40
Create Date: 2026-11-07 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6d2e4f8a9b10"
down_revision: str | None = "3a7c9e1f2b40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("demand_profiles", sa.Column("sales_load", sa.JSON(), nullable=True))
    op.execute("UPDATE demand_profiles SET source = 'sales' WHERE source = 'freshretailnet'")


def downgrade() -> None:
    op.execute("UPDATE demand_profiles SET source = 'freshretailnet' WHERE source = 'sales'")
    op.drop_column("demand_profiles", "sales_load")
