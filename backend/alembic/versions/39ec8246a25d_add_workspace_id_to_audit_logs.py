"""add workspace_id to audit_logs

Revision ID: 39ec8246a25d
Revises: 1425364066f2
Create Date: 2026-02-28 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "39ec8246a25d"
down_revision: Union[str, Sequence[str], None] = "1425364066f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "audit_logs" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("audit_logs")}
    if "workspace_id" not in cols:
        op.add_column("audit_logs", sa.Column("workspace_id", sa.Integer(), nullable=True))

    # Create index if missing
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("audit_logs")}
    ix_name = op.f("ix_audit_logs_workspace_id")
    if ix_name not in existing_indexes:
        op.create_index(ix_name, "audit_logs", ["workspace_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "audit_logs" not in tables:
        return

    existing_indexes = {ix["name"] for ix in inspector.get_indexes("audit_logs")}
    ix_name = op.f("ix_audit_logs_workspace_id")
    if ix_name in existing_indexes:
        op.drop_index(ix_name, table_name="audit_logs")

    cols = {c["name"] for c in inspector.get_columns("audit_logs")}
    if "workspace_id" in cols:
        op.drop_column("audit_logs", "workspace_id")