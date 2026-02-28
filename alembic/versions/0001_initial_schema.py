"""initial schema (consolidated for SQLite)

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-28

This consolidated migration creates the final schema directly,
replacing the incremental PostgreSQL migrations for SQLite compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001_initial'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # clan_logs table
    op.create_table(
        "clan_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("clan_name", sa.String(), nullable=False),
        sa.Column("member_username", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("log_type", sa.String(), nullable=False, server_default="unknown"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clan_name", "member_username", "message", "timestamp",
            name="uq_clan_log_identity",
        ),
    )

    # scheduled_messages table
    op.create_table(
        "scheduled_messages",
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("channel_id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("type", "channel_id"),
    )


def downgrade() -> None:
    op.drop_table("scheduled_messages")
    op.drop_table("clan_logs")
