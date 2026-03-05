"""create approvals and audit logs

Revision ID: 399f3e0a94c3
Revises: None
Create Date: 2026-02-27 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "399f3e0a94c3"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    # ---- approvals ----
    if "approvals" not in tables:
        op.create_table(
            "approvals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("message_id", sa.String(length=128), nullable=False),
            sa.Column("thread_id", sa.String(length=128), nullable=True),
            sa.Column("from_email", sa.Text(), nullable=True),
            sa.Column("subject", sa.Text(), nullable=True),
            sa.Column("snippet", sa.Text(), nullable=True),
            sa.Column("classification_label", sa.String(length=32), nullable=True),
            sa.Column("classification_confidence", sa.String(length=16), nullable=True),
            sa.Column("classification_reason", sa.Text(), nullable=True),
            sa.Column("draft_reply", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # ---- audit_logs ----
    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("event_data", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # If your original migration created indexes, add them here with:
    # existing_indexes = {ix["name"] for ix in inspector.get_indexes("<table>")}
    # and only create if missing.


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "audit_logs" in tables:
        op.drop_table("audit_logs")
    if "approvals" in tables:
        op.drop_table("approvals")