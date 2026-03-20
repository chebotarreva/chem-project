"""Create molecules table

Revision ID: ea94da5d9cce
Revises: 7defcd0eb203
Create Date: 2026-01-09 13:18:12.479838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea94da5d9cce'
down_revision: Union[str, Sequence[str], None] = '7defcd0eb203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
