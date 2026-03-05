"""add workspace_id to audit_logs

Revision ID: c699aed70586
Revises: 39ec8246a25d
Create Date: 2026-02-26 22:18:06.176019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c699aed70586'
down_revision: Union[str, Sequence[str], None] = '39ec8246a25d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
