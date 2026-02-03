from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ClanMessage(Base):
    __tablename__ = "clan_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clan_name: Mapped[str] = mapped_column(nullable=False)
    member_username: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    message_sent: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        UniqueConstraint(
            "clan_name", "member_username", "message", "timestamp",
            name="uq_clan_message_identity",
        ),
    )
