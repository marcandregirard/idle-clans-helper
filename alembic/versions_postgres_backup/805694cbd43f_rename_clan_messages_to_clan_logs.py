"""rename clan_messages to clan_logs

Revision ID: 805694cbd43f
Revises: 1828a5fe98c2
Create Date: 2026-02-04 21:23:50.873547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '805694cbd43f'
down_revision: Union[str, Sequence[str], None] = '1828a5fe98c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("clan_messages", "clan_logs")
    with op.batch_alter_table("clan_logs") as batch_op:
        batch_op.drop_constraint("uq_clan_message_identity", type_="unique")
        batch_op.create_unique_constraint(
            "uq_clan_log_identity",
            ["clan_name", "member_username", "message", "timestamp"],
        )


def downgrade() -> None:
    with op.batch_alter_table("clan_logs") as batch_op:
        batch_op.drop_constraint("uq_clan_log_identity", type_="unique")
        batch_op.create_unique_constraint(
            "uq_clan_message_identity",
            ["clan_name", "member_username", "message", "timestamp"],
        )
    op.rename_table("clan_logs", "clan_messages")
