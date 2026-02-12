"""add player_xp_snapshots table

Revision ID: a1b2c3d4e5f6
Revises: 889230bd6280
Create Date: 2026-02-12 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "889230bd6280"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "player_xp_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_name", sa.String(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attack", sa.BigInteger(), nullable=False),
        sa.Column("strength", sa.BigInteger(), nullable=False),
        sa.Column("defence", sa.BigInteger(), nullable=False),
        sa.Column("archery", sa.BigInteger(), nullable=False),
        sa.Column("magic", sa.BigInteger(), nullable=False),
        sa.Column("health", sa.BigInteger(), nullable=False),
        sa.Column("exterminating", sa.BigInteger(), nullable=False),
        sa.Column("woodcutting", sa.BigInteger(), nullable=False),
        sa.Column("fishing", sa.BigInteger(), nullable=False),
        sa.Column("mining", sa.BigInteger(), nullable=False),
        sa.Column("foraging", sa.BigInteger(), nullable=False),
        sa.Column("farming", sa.BigInteger(), nullable=False),
        sa.Column("crafting", sa.BigInteger(), nullable=False),
        sa.Column("carpentry", sa.BigInteger(), nullable=False),
        sa.Column("cooking", sa.BigInteger(), nullable=False),
        sa.Column("smithing", sa.BigInteger(), nullable=False),
        sa.Column("brewing", sa.BigInteger(), nullable=False),
        sa.Column("enchanting", sa.BigInteger(), nullable=False),
        sa.Column("agility", sa.BigInteger(), nullable=False),
        sa.Column("plundering", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_player_xp_snapshot_player_time",
        "player_xp_snapshots",
        ["player_name", "fetched_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_player_xp_snapshot_player_time", table_name="player_xp_snapshots")
    op.drop_table("player_xp_snapshots")
