from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.player import Player


class PeerReview(Base):
    __tablename__ = "peer_reviews"
    __table_args__ = (
        UniqueConstraint(
            "reviewer_id", "reviewed_player_id", "match_id", name="uq_peer_review_per_match"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewed_player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Sport-specific sub-ratings stored as JSONB
    # Soccer:      {"defending": 1-5, "attacking": 1-5, "teamwork": 1-5, "effort": 1-5}
    # Basketball:  {"defense": 1-5, "offense": 1-5, "communication": 1-5, "effort": 1-5}
    ratings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reviewer: Mapped[Player] = relationship(
        "Player", foreign_keys=[reviewer_id], back_populates="reviews_given"
    )
    reviewed_player: Mapped[Player] = relationship(
        "Player", foreign_keys=[reviewed_player_id], back_populates="reviews_received"
    )
    match: Mapped[Match] = relationship("Match", back_populates="peer_reviews")
