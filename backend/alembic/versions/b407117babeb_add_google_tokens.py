"""add google tokens

Revision ID: b407117babeb
Revises: 35793e5fda87
Create Date: 2026-02-27 09:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "b407117babeb"
down_revision: Union[str, Sequence[str], None] = "35793e5fda87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    # Create google_tokens only if it does not already exist
    if "google_tokens" not in tables:
        op.create_table(
            "google_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("workspace_id", sa.Integer(), nullable=True),
            sa.Column("token", sa.Text(), nullable=True),
            sa.Column("refresh_token", sa.Text(), nullable=True),
            sa.Column("token_uri", sa.Text(), nullable=True),
            sa.Column("client_id", sa.Text(), nullable=True),
            sa.Column("client_secret", sa.Text(), nullable=True),
            sa.Column("scopes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # If you have indexes/constraints in the original migration, add them here
    # with the same "if index not exists" pattern.


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "google_tokens" in tables:
        op.drop_table("google_tokens")