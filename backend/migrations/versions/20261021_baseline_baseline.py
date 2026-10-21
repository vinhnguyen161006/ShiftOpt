"""baseline

Revision ID: baseline
Revises:
Create Date: 2026-10-21 13:41:02.348048
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demand_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "manual",
                "csv",
                "freshretailnet",
                "call_center",
                name="demandsource",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "mode",
            sa.Enum("linear", "erlang", name="staffingmode", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("required_staff", sa.JSON(), nullable=False),
        sa.Column("conversion_params", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_demand_profiles")),
        sa.UniqueConstraint("name", name=op.f("uq_demand_profiles_name")),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("hourly_wage", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employees")),
        sa.UniqueConstraint("code", name=op.f("uq_employees_code")),
    )
    op.create_table(
        "shift_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("start_hour", sa.Integer(), nullable=False),
        sa.Column("length_hours", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shift_templates")),
        sa.UniqueConstraint("name", name=op.f("uq_shift_templates_name")),
    )
    op.create_table(
        "solve_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("demand_profile_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "succeeded",
                "failed",
                name="runstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("solver", sa.String(length=64), nullable=False),
        sa.Column("solve_status", sa.String(length=32), nullable=True),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("instance_snapshot", sa.JSON(), nullable=False),
        sa.Column("assignments", sa.JSON(), nullable=True),
        sa.Column("objective", sa.Double(), nullable=True),
        sa.Column("best_bound", sa.Double(), nullable=True),
        sa.Column("gap", sa.Double(), nullable=True),
        sa.Column("understaffed_hours", sa.Integer(), nullable=True),
        sa.Column("wall_time_seconds", sa.Double(), nullable=True),
        sa.Column("solver_log", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["demand_profile_id"],
            ["demand_profiles.id"],
            name=op.f("fk_solve_runs_demand_profile_id_demand_profiles"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solve_runs")),
    )
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "demand_sweep",
                "marginal_cost",
                "lp_duals",
                name="analysiskind",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("base_run_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "succeeded",
                "failed",
                name="runstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["base_run_id"],
            ["solve_runs.id"],
            name=op.f("fk_analysis_runs_base_run_id_solve_runs"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_runs")),
    )


def downgrade() -> None:
    op.drop_table("analysis_runs")
    op.drop_table("solve_runs")
    op.drop_table("shift_templates")
    op.drop_table("employees")
    op.drop_table("demand_profiles")
