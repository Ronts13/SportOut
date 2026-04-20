from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.player import Player


class SportProfile(Base):
    __tablename__ = "sport_profiles"
    __table_args__ = (
        UniqueConstraint("player_id", "sport", name="uq_sport_profiles_player_sport"),
        # Composite index for leaderboard and matchmaking range queries
        Index("ix_sport_profiles_sport_rating", "sport", "current_rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_position: Mapped[str | None] = mapped_column(String(32))
    secondary_positions: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    # Denormalized from rating_events — updated by rating worker after each game
    current_rating: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    career_games: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    career_wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    player: Mapped[Player] = relationship("Player", back_populates="sport_profiles")
