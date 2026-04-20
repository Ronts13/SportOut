from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Time, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.user import User


class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (Index("ix_facilities_location", "location", postgresql_using="gist"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    address_street: Mapped[str] = mapped_column(String(200), nullable=False)
    address_city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_country: Mapped[str] = mapped_column(String(3), nullable=False, default="IL")
    sports_supported: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)

    # Operating hours — stored for the "exact hours" survey request
    opens_at: Mapped[time | None] = mapped_column(Time(timezone=False))
    closes_at: Mapped[time | None] = mapped_column(Time(timezone=False))
    operating_days: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)  # 0=Mon..6=Sun

    amenities: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    manager: Mapped[User | None] = relationship("User", back_populates="managed_facilities")
    courts: Mapped[list[Court]] = relationship(
        "Court", back_populates="facility", cascade="all, delete-orphan"
    )
    matches: Mapped[list[Match]] = relationship("Match", back_populates="facility")


class Court(Base):
    __tablename__ = "courts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    surface: Mapped[str] = mapped_column(String(32), nullable=False, default="asphalt")
    indoor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Live state fields — top survey requests for "Live Courts" map feature
    lighting_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lighting_on: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    condition: Mapped[str] = mapped_column(String(32), nullable=False, default="good")
    condition_note: Mapped[str | None] = mapped_column(String(300))

    is_bookable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    facility: Mapped[Facility] = relationship("Facility", back_populates="courts")
    availability_slots: Mapped[list[AvailabilitySlot]] = relationship(
        "AvailabilitySlot", back_populates="court", cascade="all, delete-orphan"
    )
    matches: Mapped[list[Match]] = relationship("Match", back_populates="court")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    __table_args__ = (Index("ix_availability_slots_court_start", "court_id", "starts_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    court_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    booked_by_match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL")
    )

    court: Mapped[Court] = relationship("Court", back_populates="availability_slots")
