"""approval action support

Revision ID: ac1cafd20128
Revises: d0bedbd3b532
Create Date: 2026-03-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "ac1cafd20128"
down_revision: Union[str, Sequence[str], None] = "d0bedbd3b532"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "approvals" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("approvals")}
    if "action_type" not in cols:
        op.add_column("approvals", sa.Column("action_type", sa.String(length=32), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "approvals" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("approvals")}
    if "action_type" in cols:
        op.drop_column("approvals", "action_type")