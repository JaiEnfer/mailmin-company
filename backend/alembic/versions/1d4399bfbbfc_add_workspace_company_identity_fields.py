"""add workspace company identity fields

Revision ID: 1d4399bfbbfc
Revises: 3225c43b3b3b
Create Date: 2026-03-04 20:36:44.822375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d4399bfbbfc'
down_revision: Union[str, Sequence[str], None] = '3225c43b3b3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("workspaces", sa.Column("company_display_name", sa.String(), nullable=True))
    op.add_column("workspaces", sa.Column("company_email", sa.String(), nullable=True))
    op.add_column("workspaces", sa.Column("company_address", sa.Text(), nullable=True))
    op.add_column("workspaces", sa.Column("company_phone", sa.String(), nullable=True))
    op.add_column("workspaces", sa.Column("signature_style", sa.String(), server_default="team", nullable=False))
    op.add_column("workspaces", sa.Column("signature_name", sa.String(), nullable=True))

def downgrade():
    op.drop_column("workspaces", "signature_name")
    op.drop_column("workspaces", "signature_style")
    op.drop_column("workspaces", "company_phone")
    op.drop_column("workspaces", "company_address")
    op.drop_column("workspaces", "company_email")
    op.drop_column("workspaces", "company_display_name")
