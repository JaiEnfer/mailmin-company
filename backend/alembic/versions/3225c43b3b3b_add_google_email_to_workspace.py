"""Add google_email to workspaces and token_json to google_tokens (if missing)

Revision ID: 3225c43b3b3b
Revises: 5d6c26d92e0a
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "3225c43b3b3b"
down_revision = "5d6c26d92e0a"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = inspect(conn)
    tables = set(insp.get_table_names())

    # workspaces.google_email
    if "workspaces" in tables:
        cols = {c["name"] for c in insp.get_columns("workspaces")}
        if "google_email" not in cols:
            op.add_column(
                "workspaces",
                sa.Column("google_email", sa.Text(), nullable=True),
            )

    # google_tokens.token_json (add if missing; do NOT alter NOT NULL here)
    if "google_tokens" in tables:
        cols = {c["name"] for c in insp.get_columns("google_tokens")}
        if "token_json" not in cols:
            op.add_column(
                "google_tokens",
                sa.Column("token_json", sa.Text(), nullable=True),
            )


def downgrade():
    conn = op.get_bind()
    insp = inspect(conn)
    tables = set(insp.get_table_names())

    if "workspaces" in tables:
        cols = {c["name"] for c in insp.get_columns("workspaces")}
        if "google_email" in cols:
            op.drop_column("workspaces", "google_email")

    if "google_tokens" in tables:
        cols = {c["name"] for c in insp.get_columns("google_tokens")}
        if "token_json" in cols:
            op.drop_column("google_tokens", "token_json")