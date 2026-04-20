from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MatchCreate(BaseModel):
    sport: str
    facility_id: uuid.UUID | None = None
    court_id: uuid.UUID | None = None
    scheduled_at: datetime
    format: str = "pickup"
    is_private: bool = False
    min_rating: float | None = Field(None, ge=0)
    max_rating: float | None = Field(None, ge=0)
    max_players: int = Field(10, ge=2, le=30)

    @model_validator(mode="after")
    def validate_rating_bracket(self) -> MatchCreate:
        if self.min_rating is not None and self.max_rating is not None:
            if self.min_rating > self.max_rating:
                raise ValueError("min_rating must be <= max_rating")
        return self


class MatchRosterEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    player_id: uuid.UUID
    team: str
    confirmed: bool
    attended: bool | None
    joined_at: datetime


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sport: str
    facility_id: uuid.UUID | None
    court_id: uuid.UUID | None
    created_by_id: uuid.UUID | None
    scheduled_at: datetime
    status: str
    format: str
    is_private: bool
    min_rating: float | None
    max_rating: float | None
    max_players: int
    home_score: int | None
    away_score: int | None
    mvp_player_id: uuid.UUID | None
    created_at: datetime
    rosters: list[MatchRosterEntryOut] = []


class MatchResultSubmit(BaseModel):
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    mvp_player_id: uuid.UUID | None = None


class PlayerGameStatsCreate(BaseModel):
    match_roster_id: uuid.UUID
    sport: str
    # Raw dict validated against sports.registry.STAT_SCHEMAS[sport] in the service layer
    stats: dict
