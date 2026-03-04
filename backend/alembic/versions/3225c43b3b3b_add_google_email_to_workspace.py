"""Add google_email to workspace

Revision ID: 3225c43b3b3b
Revises: 5d6c26d92e0a
Create Date: 2026-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "3225c43b3b3b"
down_revision: Union[str, Sequence[str], None] = "5d6c26d92e0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    tables = inspector.get_table_names()

    # ----------------------------------------------------
    # 1. Add google_email to workspaces if missing
    # ----------------------------------------------------
    if "workspaces" in tables:
        columns = [c["name"] for c in inspector.get_columns("workspaces")]

        if "google_email" not in columns:
            op.add_column(
                "workspaces",
                sa.Column("google_email", sa.Text(), nullable=True)
            )

    # ----------------------------------------------------
    # 2. Ensure google_tokens.token_json exists
    # ----------------------------------------------------
    if "google_tokens" in tables:
        columns = [c["name"] for c in inspector.get_columns("google_tokens")]

        if "token_json" not in columns:
            op.add_column(
                "google_tokens",
                sa.Column("token_json", sa.Text(), nullable=True)
            )


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    tables = inspector.get_table_names()

    if "workspaces" in tables:
        columns = [c["name"] for c in inspector.get_columns("workspaces")]
        if "google_email" in columns:
            op.drop_column("workspaces", "google_email")

    if "google_tokens" in tables:
        columns = [c["name"] for c in inspector.get_columns("google_tokens")]
        if "token_json" in columns:
            op.drop_column("google_tokens", "token_json")