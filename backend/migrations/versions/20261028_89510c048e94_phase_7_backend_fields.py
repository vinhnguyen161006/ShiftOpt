"""phase 7 backend fields

Revision ID: 89510c048e94
Revises: baseline
Create Date: 2026-10-28 10:18:38.351627
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "89510c048e94"
down_revision: str | None = "baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "demand_profiles",
        sa.Column(
            "source_metadata", sa.JSON(), nullable=False, server_default=sa.text("(JSON_OBJECT())")
        ),
    )
    op.add_column(
        "employees",
        sa.Column(
            "unavailable_days", sa.JSON(), nullable=False, server_default=sa.text("(JSON_ARRAY())")
        ),
    )
    op.add_column(
        "employees",
        sa.Column(
            "preferred_days_off",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("(JSON_ARRAY())"),
        ),
    )
    op.add_column("solve_runs", sa.Column("parent_run_id", sa.Integer(), nullable=True))
    op.add_column("solve_runs", sa.Column("solver_version", sa.String(length=64), nullable=True))
    op.add_column("solve_runs", sa.Column("hard_violations", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_solve_runs_parent_run_id_solve_runs"),
        "solve_runs",
        "solve_runs",
        ["parent_run_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_solve_runs_parent_run_id_solve_runs"), "solve_runs", type_="foreignkey"
    )
    op.drop_column("solve_runs", "hard_violations")
    op.drop_column("solve_runs", "solver_version")
    op.drop_column("solve_runs", "parent_run_id")
    op.drop_column("employees", "preferred_days_off")
    op.drop_column("employees", "unavailable_days")
    op.drop_column("demand_profiles", "source_metadata")
