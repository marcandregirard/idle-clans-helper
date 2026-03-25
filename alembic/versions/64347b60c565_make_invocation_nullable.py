"""make invocation nullable

Revision ID: 64347b60c565
Revises: cf87d76be25c
Create Date: 2026-03-25 16:30:11.745045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64347b60c565'
down_revision: Union[str, Sequence[str], None] = 'cf87d76be25c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('player_xp_snapshots', 'invocation', existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column('player_xp_snapshots', 'invocation', existing_type=sa.BigInteger(), nullable=False)
