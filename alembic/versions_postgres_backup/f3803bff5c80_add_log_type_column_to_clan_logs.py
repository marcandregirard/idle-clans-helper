"""add log_type column to clan_logs

Revision ID: f3803bff5c80
Revises: 805694cbd43f
Create Date: 2026-02-04 21:29:02.413300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3803bff5c80'
down_revision: Union[str, Sequence[str], None] = '805694cbd43f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clan_logs",
        sa.Column("log_type", sa.String(), nullable=False, server_default="unknown"),
    )


def downgrade() -> None:
    op.drop_column("clan_logs", "log_type")
