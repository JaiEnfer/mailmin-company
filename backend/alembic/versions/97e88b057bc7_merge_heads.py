"""merge heads

Revision ID: 97e88b057bc7
Revises: 399f3e0a94c3, ac1cafd20128
Create Date: 2026-03-05 12:20:50.368903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97e88b057bc7'
down_revision: Union[str, Sequence[str], None] = ('399f3e0a94c3', 'ac1cafd20128')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
