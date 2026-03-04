"""Add google_email to workspace

Revision ID: 3225c43b3b3b
Revises: 5d6c26d92e0a
Create Date: 2026-03-02 20:53:23.546742
"""
from typing import Sequence, Union, Set

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "3225c43b3b3b"
down_revision: Union[str, Sequence[str], None] = "5d6c26d92e0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) workspaces.google_email (safe add)
    with op.batch_alter_table("workspaces") as batch_op:
        if not _has_column("workspaces", "google_email"):
            batch_op.add_column(sa.Column("google_email", sa.Text(), nullable=True))

    # 2) Ensure google_tokens.token_json exists (safe, no NOT NULL here)
    if _has_table("google_tokens") and not _has_column("google_tokens", "token_json"):
        with op.batch_alter_table("google_tokens") as batch_op:
            batch_op.add_column(sa.Column("token_json", sa.Text(), nullable=True))


def downgrade():
    # workspaces.google_email
    if _has_table("workspaces") and _has_column("workspaces", "google_email"):
        with op.batch_alter_table("workspaces") as batch_op:
            batch_op.drop_column("google_email")

    # google_tokens.token_json
    if _has_table("google_tokens") and _has_column("google_tokens", "token_json"):
        with op.batch_alter_table("google_tokens") as batch_op:
            batch_op.drop_column("token_json")


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def _get_columns(table_name: str) -> Set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    return {c["name"] for c in insp.get_columns(table_name)}


def _has_column(table_name: str, col_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return col_name in _get_columns(table_name)