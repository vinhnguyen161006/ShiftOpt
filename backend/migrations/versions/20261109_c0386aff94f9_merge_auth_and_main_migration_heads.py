"""merge auth and main migration heads

Revision ID: c0386aff94f9
Revises: 8c4a2e9d6f31, b7c8d9e0f1a2
Create Date: 2026-11-09 15:14:27.445687
"""

from collections.abc import Sequence

revision: str = "c0386aff94f9"
down_revision: str | None = ("8c4a2e9d6f31", "b7c8d9e0f1a2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
