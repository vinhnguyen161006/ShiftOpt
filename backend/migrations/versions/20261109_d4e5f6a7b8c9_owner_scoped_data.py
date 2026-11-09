"""owner scoped data

Every working row belongs to one account. Rows that exist before this revision go to the
account whose email is SHIFTOPT_DEMO_EMAIL, or to the oldest account when that variable is not
set or matches nobody. The upgrade stops, changing nothing, when rows exist but no account does.
Downgrade restores the global unique keys and fails if two accounts share a code or name.

Revision ID: d4e5f6a7b8c9
Revises: c0386aff94f9
Create Date: 2026-11-09 18:00:00.000000

"""

import os
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c0386aff94f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNED_TABLES = ("demand_profiles", "employees", "shift_templates", "solve_runs", "analysis_runs")
UNIQUE_KEYS = (("demand_profiles", "name"), ("employees", "code"), ("shift_templates", "name"))


def _existing_owner(connection: sa.Connection) -> int | None:
    email = os.environ.get("SHIFTOPT_DEMO_EMAIL", "").strip().lower()
    if email:
        owner = connection.execute(
            sa.text("SELECT id FROM users WHERE email = :email"), {"email": email}
        ).scalar()
        if owner is not None:
            return int(owner)
    oldest = connection.execute(sa.text("SELECT MIN(id) FROM users")).scalar()
    return None if oldest is None else int(oldest)


def _has_rows(connection: sa.Connection) -> bool:
    return any(
        connection.execute(sa.select(sa.func.count()).select_from(sa.table(table))).scalar()
        for table in OWNED_TABLES
    )


def upgrade() -> None:
    connection = op.get_bind()
    owner = _existing_owner(connection)
    if owner is None and _has_rows(connection):
        raise RuntimeError(
            "existing rows need an owner: create an account first, then run the upgrade again"
        )
    for table in OWNED_TABLES:
        op.add_column(table, sa.Column("owner_id", sa.Integer(), nullable=True))
        if owner is not None:
            connection.execute(
                sa.update(sa.table(table, sa.column("owner_id"))).values(owner_id=owner)
            )
        op.alter_column(table, "owner_id", existing_type=sa.Integer(), nullable=False)
        op.create_index(op.f(f"ix_{table}_owner_id"), table, ["owner_id"])
        op.create_foreign_key(
            op.f(f"fk_{table}_owner_id_users"),
            table,
            "users",
            ["owner_id"],
            ["id"],
            ondelete="CASCADE",
        )
    for table, column in UNIQUE_KEYS:
        op.drop_constraint(op.f(f"uq_{table}_{column}"), table, type_="unique")
        op.create_unique_constraint(op.f(f"uq_{table}_owner_id"), table, ["owner_id", column])


def downgrade() -> None:
    for table, column in UNIQUE_KEYS:
        op.drop_constraint(op.f(f"uq_{table}_owner_id"), table, type_="unique")
        op.create_unique_constraint(op.f(f"uq_{table}_{column}"), table, [column])
    for table in OWNED_TABLES:
        op.drop_constraint(op.f(f"fk_{table}_owner_id_users"), table, type_="foreignkey")
        op.drop_index(op.f(f"ix_{table}_owner_id"), table_name=table)
        op.drop_column(table, "owner_id")
