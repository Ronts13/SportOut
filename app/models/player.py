from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import MatchRoster
    from app.models.media import Highlight
    from app.models.peer_review import PeerReview
    from app.models.rating import RatingEvent
    from app.models.sport_profile import SportProfile
    from app.models.user import User


class PlayerFollow(Base):
    __tablename__ = "player_follows"
    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="uq_follow_pair"),)

    follower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), primary_key=True
    )
    followed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    banner_url: Mapped[str | None] = mapped_column(String(512))
    bio: Mapped[str | None] = mapped_column(String(500))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    location: Mapped[object | None] = mapped_column(Geometry("POINT", srid=4326))
    city: Mapped[str | None] = mapped_column(String(100))
    card_is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Denormalized counters — updated by trigger or service layer on follow/unfollow
    follower_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    following_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship("User", back_populates="player")
    sport_profiles: Mapped[list[SportProfile]] = relationship(
        "SportProfile", back_populates="player", cascade="all, delete-orphan"
    )
    match_rosters: Mapped[list[MatchRoster]] = relationship("MatchRoster", back_populates="player")
    highlights: Mapped[list[Highlight]] = relationship(
        "Highlight", back_populates="player", order_by="Highlight.generated_at.desc()"
    )
    rating_events: Mapped[list[RatingEvent]] = relationship("RatingEvent", back_populates="player")
    reviews_given: Mapped[list[PeerReview]] = relationship(
        "PeerReview", foreign_keys="PeerReview.reviewer_id", back_populates="reviewer"
    )
    reviews_received: Mapped[list[PeerReview]] = relationship(
        "PeerReview", foreign_keys="PeerReview.reviewed_player_id", back_populates="reviewed_player"
    )

    # Social graph — self-referential M2M via PlayerFollow association
    following: Mapped[list[Player]] = relationship(
        "Player",
        secondary="player_follows",
        primaryjoin="Player.id == PlayerFollow.follower_id",
        secondaryjoin="Player.id == PlayerFollow.followed_id",
        viewonly=True,
    )
    followers: Mapped[list[Player]] = relationship(
        "Player",
        secondary="player_follows",
        primaryjoin="Player.id == PlayerFollow.followed_id",
        secondaryjoin="Player.id == PlayerFollow.follower_id",
        viewonly=True,
    )
