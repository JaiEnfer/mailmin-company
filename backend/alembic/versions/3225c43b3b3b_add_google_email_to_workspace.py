"""Add google_email to workspaces (safe)

Revision ID: 3225c43b3b3b
Revises: <PUT_YOUR_REAL_HEAD_HERE>
Create Date: 2026-03-02
"""
from __future__ import annotations

from typing import Sequence, Union, Set

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# IMPORTANT:
# - revision must match filename prefix
# - down_revision must be a revision that EXISTS in your repo
revision: str = "3225c43b3b3b"
down_revision: Union[str, Sequence[str], None] = "93496fa0940d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    # 1) Add workspaces.google_email (nullable)
    if "workspaces" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("workspaces")}
        if "google_email" not in cols:
            with op.batch_alter_table("workspaces") as b:
                b.add_column(sa.Column("google_email", sa.Text(), nullable=True))

    # 2) Ensure google_tokens.token_json exists (nullable)
    # Some DBs may have google_tokens but missing token_json due to earlier schema drift
    if "google_tokens" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("google_tokens")}
        if "token_json" not in cols:
            with op.batch_alter_table("google_tokens") as b:
                b.add_column(sa.Column("token_json", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    if "workspaces" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("workspaces")}
        if "google_email" in cols:
            with op.batch_alter_table("workspaces") as b:
                b.drop_column("google_email")

    if "google_tokens" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("google_tokens")}
        if "token_json" in cols:
            with op.batch_alter_table("google_tokens") as b:
                b.drop_column("token_json")