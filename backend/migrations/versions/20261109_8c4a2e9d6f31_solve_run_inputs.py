"""solve run source inputs and input hash

Revision ID: 8c4a2e9d6f31
Revises: 5b8d1f3a7c20
Create Date: 2026-11-09 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c4a2e9d6f31"
down_revision: str | None = "5b8d1f3a7c20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("solve_runs", sa.Column("source_inputs", sa.JSON(), nullable=True))
    op.add_column("solve_runs", sa.Column("input_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("solve_runs", "input_hash")
    op.drop_column("solve_runs", "source_inputs")
