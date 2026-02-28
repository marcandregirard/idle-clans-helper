"""create clan_messages table

Revision ID: 1828a5fe98c2
Revises: 
Create Date: 2026-02-03 11:08:31.827626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1828a5fe98c2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clan_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clan_name", sa.String(), nullable=False),
        sa.Column("member_username", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("message_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clan_name", "member_username", "message", "timestamp",
            name="uq_clan_message_identity",
        ),
    )


def downgrade() -> None:
    op.drop_table("clan_messages")
