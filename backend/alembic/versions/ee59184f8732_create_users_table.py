"""create users table

Revision ID: ee59184f8732
Revises: 97e88b057bc7
Create Date: 2026-03-05 12:43:58.756026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee59184f8732'
down_revision: Union[str, Sequence[str], None] = '97e88b057bc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
