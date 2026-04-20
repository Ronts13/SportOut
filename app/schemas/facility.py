from __future__ import annotations

import uuid
from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


class CourtLiveUpdate(BaseModel):
    """Payload for a facility manager to push real-time court state changes."""
    lighting_on: bool | None = None
    current_occupancy: int | None = Field(None, ge=0)
    condition: str | None = None
    condition_note: str | None = Field(None, max_length=300)


class CourtOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    name: str
    sport: str
    surface: str
    indoor: bool
    lighting_available: bool
    lighting_on: bool
    current_occupancy: int
    max_capacity: int
    condition: str
    condition_note: str | None
    is_bookable: bool
    updated_at: datetime


class FacilityCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address_street: str = Field(..., max_length=200)
    address_city: str = Field(..., max_length=100)
    sports_supported: list[str] = Field(default_factory=list)
    opens_at: time | None = None
    closes_at: time | None = None
    operating_days: list[int] = Field(default_factory=list)
    amenities: dict = Field(default_factory=dict)


class FacilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address_street: str
    address_city: str
    latitude: float
    longitude: float
    sports_supported: list[str]
    opens_at: time | None
    closes_at: time | None
    operating_days: list[int]
    amenities: dict
    is_active: bool
    courts: list[CourtOut] = []
