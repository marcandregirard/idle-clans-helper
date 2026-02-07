from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class MessageType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BOSS_SUMMARY = "bosssummary"


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    type: Mapped[str] = mapped_column(nullable=False, primary_key=True)
    channel_id: Mapped[str] = mapped_column(nullable=False, primary_key=True)
    message_id: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        PrimaryKeyConstraint("type", "channel_id", name="pk_scheduled_message"),
    )
