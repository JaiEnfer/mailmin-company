"""add workspaces

Revision ID: 35793e5fda87
Revises: 27b8a464f9e5
Create Date: 2026-02-26 21:26:11.143637
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "35793e5fda87"
down_revision: Union[str, Sequence[str], None] = "3225c43b3b3b"  # patched from missing 27b8a464f9e5
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # ---- workspaces table + its indexes (create only if missing) ----
    existing_tables = set(inspector.get_table_names())

    if "workspaces" not in existing_tables:
        op.create_table(
            "workspaces",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_workspaces_id"), "workspaces", ["id"], unique=False)
        op.create_index(op.f("ix_workspaces_name"), "workspaces", ["name"], unique=True)
    else:
        # Table exists; make sure indexes exist before trying to create them
        # (important for DBs that already have a richer schema)
        existing_indexes = {ix["name"] for ix in inspector.get_indexes("workspaces")}

        ix_id = op.f("ix_workspaces_id")
        if ix_id not in existing_indexes:
            op.create_index(ix_id, "workspaces", ["id"], unique=False)

    # ---- approvals.workspace_id column + index (add only if missing) ----
    if "approvals" in existing_tables:
        approvals_cols = {c["name"] for c in inspector.get_columns("approvals")}

        if "workspace_id" not in approvals_cols:
            op.add_column("approvals", sa.Column("workspace_id", sa.Integer(), nullable=True))

        approvals_indexes = {ix["name"] for ix in inspector.get_indexes("approvals")}
        ix_approvals_ws = op.f("ix_approvals_workspace_id")
        if ix_approvals_ws not in approvals_indexes:
            op.create_index(ix_approvals_ws, "approvals", ["workspace_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Reverse of approvals changes (only if present)
    if "approvals" in existing_tables:
        approvals_cols = {c["name"] for c in inspector.get_columns("approvals")}
        approvals_indexes = {ix["name"] for ix in inspector.get_indexes("approvals")}

        ix_approvals_ws = op.f("ix_approvals_workspace_id")
        if ix_approvals_ws in approvals_indexes:
            op.drop_index(ix_approvals_ws, table_name="approvals")

        if "workspace_id" in approvals_cols:
            op.drop_column("approvals", "workspace_id")

    # Reverse workspaces changes (only if present)
    if "workspaces" in existing_tables:
        workspaces_indexes = {ix["name"] for ix in inspector.get_indexes("workspaces")}

        ix_name = op.f("ix_workspaces_name")
        if ix_name in workspaces_indexes:
            op.drop_index(ix_name, table_name="workspaces")

        ix_id = op.f("ix_workspaces_id")
        if ix_id in workspaces_indexes:
            op.drop_index(ix_id, table_name="workspaces")

        op.drop_table("workspaces")