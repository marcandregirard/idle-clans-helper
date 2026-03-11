from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class PlayerXpSnapshot(Base):
    __tablename__ = "player_xp_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Combat skills
    attack: Mapped[int] = mapped_column(BigInteger, nullable=False)
    strength: Mapped[int] = mapped_column(BigInteger, nullable=False)
    defence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    archery: Mapped[int] = mapped_column(BigInteger, nullable=False)
    magic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    health: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exterminating: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Gathering skills
    woodcutting: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fishing: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mining: Mapped[int] = mapped_column(BigInteger, nullable=False)
    foraging: Mapped[int] = mapped_column(BigInteger, nullable=False)
    farming: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Crafting skills
    crafting: Mapped[int] = mapped_column(BigInteger, nullable=False)
    carpentry: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cooking: Mapped[int] = mapped_column(BigInteger, nullable=False)
    smithing: Mapped[int] = mapped_column(BigInteger, nullable=False)
    brewing: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enchanting: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Other skills
    agility: Mapped[int] = mapped_column(BigInteger, nullable=False)
    plundering: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("ix_player_xp_snapshot_player_time", "player_name", "fetched_at"),
    )
