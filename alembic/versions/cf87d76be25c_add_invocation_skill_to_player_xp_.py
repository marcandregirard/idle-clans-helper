"""add invocation skill to player_xp_snapshot

Revision ID: cf87d76be25c
Revises: a1b2c3d4e5f6
Create Date: 2026-03-25 13:56:21.514909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf87d76be25c'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('player_xp_snapshots', sa.Column('invocation', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('player_xp_snapshots', 'invocation')
