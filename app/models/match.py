from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.facility import Court, Facility
    from app.models.media import MediaSession
    from app.models.peer_review import PeerReview
    from app.models.player import Player
    from app.models.rating import RatingEvent


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_sport_status_scheduled", "sport", "status", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    facility_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL")
    )
    court_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courts.id", ondelete="SET NULL")
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", index=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="pickup")
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Matchmaking skill bracket — top survey request
    min_rating: Mapped[float | None] = mapped_column(Float)
    max_rating: Mapped[float | None] = mapped_column(Float)
    max_players: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Populated after game + result confirmation
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    mvp_player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    result_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    facility: Mapped[Facility | None] = relationship("Facility", back_populates="matches")
    court: Mapped[Court | None] = relationship("Court", back_populates="matches")
    rosters: Mapped[list[MatchRoster]] = relationship(
        "MatchRoster", back_populates="match", cascade="all, delete-orphan"
    )
    result_confirmations: Mapped[list[MatchResultConfirmation]] = relationship(
        "MatchResultConfirmation", back_populates="match", cascade="all, delete-orphan"
    )
    peer_reviews: Mapped[list[PeerReview]] = relationship("PeerReview", back_populates="match")
    rating_events: Mapped[list[RatingEvent]] = relationship("RatingEvent", back_populates="match")
    # FK lives on MediaSession side to avoid circular FK dependency
    media_session: Mapped[MediaSession | None] = relationship(
        "MediaSession", back_populates="match", uselist=False
    )


class MatchRoster(Base):
    __tablename__ = "match_rosters"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_rosters_match_player"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team: Mapped[str] = mapped_column(String(10), nullable=False, default="none")  # home | away | none
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attended: Mapped[bool | None] = mapped_column(Boolean)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match: Mapped[Match] = relationship("Match", back_populates="rosters")
    player: Mapped[Player] = relationship("Player", back_populates="match_rosters")
    game_stats: Mapped[PlayerGameStats | None] = relationship(
        "PlayerGameStats", back_populates="roster_entry", uselist=False
    )


class MatchResultConfirmation(Base):
    __tablename__ = "match_result_confirmations"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_result_confirmation_match_player"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), primary_key=True
    )
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match: Mapped[Match] = relationship("Match", back_populates="result_confirmations")


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_roster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_rosters.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    # Validated at app layer against sports.registry.STAT_SCHEMAS[sport] before insert
    stats: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roster_entry: Mapped[MatchRoster] = relationship("MatchRoster", back_populates="game_stats")
