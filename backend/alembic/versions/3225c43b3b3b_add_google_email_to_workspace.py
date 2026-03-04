"""Add google_email to workspace

Revision ID: 3225c43b3b3b
Revises: 5d6c26d92e0a
Create Date: 2026-03-02 20:53:23.546742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa, inspect


# revision identifiers, used by Alembic.
revision: str = '3225c43b3b3b'
down_revision: Union[str, Sequence[str], None] = '5d6c26d92e0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) workspaces.google_email (safe add)
    with op.batch_alter_table("workspaces") as batch_op:
        if not _has_column("workspaces", "google_email"):
            batch_op.add_column(sa.Column("google_email", sa.Text(), nullable=True))

    # 2) google_tokens.token_json mismatch between environments
    # Make migration resilient: only touch token_json if it exists; otherwise add it (nullable).
    if _has_table("google_tokens"):
        cols = _get_columns("google_tokens")

        if "token_json" in cols:
            # Only enforce NOT NULL if the column exists and data is clean.
            # Safer to leave nullable in prod to avoid breaking deploy.
            # If you *really* want NOT NULL later, do it in a separate migration after cleaning data.
            pass

        else:
            # Column doesn't exist in prod. Add it so the app code can use it consistently.
            with op.batch_alter_table("google_tokens") as batch_op:
                batch_op.add_column(sa.Column("token_json", sa.Text(), nullable=True))


def downgrade():
    # Downgrade should also be safe
    with op.batch_alter_table("workspaces") as batch_op:
        if _has_column("workspaces", "google_email"):
            batch_op.drop_column("google_email")

    if _has_table("google_tokens"):
        if _has_column("google_tokens", "token_json"):
            with op.batch_alter_table("google_tokens") as batch_op:
                batch_op.drop_column("token_json")


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def _get_columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    return {c["name"] for c in insp.get_columns(table_name)}


def _has_column(table_name: str, col_name: str) -> bool:
    return col_name in _get_columns(table_name)