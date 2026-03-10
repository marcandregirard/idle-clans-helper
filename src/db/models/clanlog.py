import re
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from ..base import Base


class UTCISODateTime(TypeDecorator):
    """Stores datetimes as 'YYYY-MM-DDTHH:MM:SSZ' text in SQLite.

    Matches the format written by the Go bot so the unique constraint
    deduplicates correctly via SQLite text comparison.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ClanLogType(StrEnum):
    COMBAT_QUEST_COMPLETED = "combat_quest_completed"
    SKILLING_QUEST_COMPLETED = "skilling_quest_completed"
    CLAN_UPGRADE = "clan_upgrade"
    VAULT_DEPOSIT = "vault_deposit"
    VAULT_WITHDRAWAL = "vault_withdrawal"
    MEMBER_JOINED = "member_joined"
    VAULT_ACCESS_GRANTED = "vault_access_granted"
    EVENT_STARTED = "event_started"
    BULLETIN_UPDATE = "bulletin_update"
    UNKNOWN = "unknown"


_TYPE_PATTERNS: list[tuple[re.Pattern, ClanLogType]] = [
    (re.compile(r"completed a combat quest"), ClanLogType.COMBAT_QUEST_COMPLETED),
    (re.compile(r"completed a skilling quest"), ClanLogType.SKILLING_QUEST_COMPLETED),
    (re.compile(r"completed a daily combat quest"), ClanLogType.COMBAT_QUEST_COMPLETED),
    (re.compile(r"bought the upgrade Gatherers"), ClanLogType.CLAN_UPGRADE),
    (re.compile(r"added \d+x .+\.$"), ClanLogType.VAULT_DEPOSIT),
    (re.compile(r"withdrew \d+x .+\.$"), ClanLogType.VAULT_WITHDRAWAL),
    (re.compile(r"has joined the clan:"), ClanLogType.MEMBER_JOINED),
    (re.compile(r"gave vault access to"), ClanLogType.VAULT_ACCESS_GRANTED),
    (re.compile(r"has started a .+ event with"), ClanLogType.EVENT_STARTED),
    (re.compile(r"updated the bulletin board"), ClanLogType.BULLETIN_UPDATE),
]


def parse_log_type(message: str) -> ClanLogType:
    for pattern, log_type in _TYPE_PATTERNS:
        if pattern.search(message):
            return log_type
    return ClanLogType.UNKNOWN


class ClanLog(Base):
    __tablename__ = "clan_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clan_name: Mapped[str] = mapped_column(nullable=False)
    member_username: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(UTCISODateTime, nullable=False)
    message_sent: Mapped[bool] = mapped_column(default=False)
    log_type: Mapped[str] = mapped_column(nullable=False, default=ClanLogType.UNKNOWN)

    __table_args__ = (
        UniqueConstraint(
            "clan_name", "member_username", "message", "timestamp",
            name="uq_clan_log_identity",
        ),
    )
