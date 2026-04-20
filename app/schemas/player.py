from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PlayerCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    date_of_birth: date | None = None
    city: str | None = Field(None, max_length=100)


class PlayerUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=2, max_length=100)
    bio: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    card_is_public: bool | None = None
    avatar_url: str | None = Field(None, max_length=512)
    banner_url: str | None = Field(None, max_length=512)


class PlayerCardOut(BaseModel):
    """Compact shareable card — used for social sharing and search results."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    username: str
    avatar_url: str | None
    city: str | None
    follower_count: int
    following_count: int


class PlayerProfileOut(PlayerCardOut):
    """Full profile — returned when viewing a player's profile page."""
    banner_url: str | None
    bio: str | None
    date_of_birth: date | None
    card_is_public: bool
    created_at: datetime


class PlayerFollowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    follower_id: uuid.UUID
    followed_id: uuid.UUID
    created_at: datetime


class LeaderboardEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    player_id: uuid.UUID
    display_name: str
    sport: str
    current_rating: float
    wins: int
    losses: int
