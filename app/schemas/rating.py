from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RatingEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    player_id: uuid.UUID
    sport: str
    match_id: uuid.UUID | None
    rating_before: float
    rating_after: float
    delta: float
    algorithm_version: str
    source_type: str
    breakdown: dict
    created_at: datetime


class RatingHistoryOut(BaseModel):
    """Time-series for a player+sport pair — drives the rating trend chart on the profile."""
    sport: str
    current_rating: float
    events: list[RatingEventOut]


class PeerReviewCreate(BaseModel):
    reviewed_player_id: uuid.UUID
    match_id: uuid.UUID
    # Keys are sport-specific (e.g. soccer: defending/attacking; basketball: defense/offense)
    ratings: dict[str, int]

    @model_validator(mode="after")
    def validate_scores(self) -> PeerReviewCreate:
        for key, val in self.ratings.items():
            if not (1 <= val <= 5):
                raise ValueError(f"Rating for '{key}' must be between 1 and 5, got {val}")
        return self


class PeerReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewed_player_id: uuid.UUID
    match_id: uuid.UUID
    ratings: dict
    is_confirmed: bool
    submitted_at: datetime
    confirmed_at: datetime | None


class CombineScoreCreate(BaseModel):
    """Admin payload for manually scoring a player's AI Combine evaluation."""
    sport: str
    # Four pillars — each scored 0–100 by the admin reviewer
    pace: int = Field(..., ge=0, le=100)
    shooting: int = Field(..., ge=0, le=100)
    dribbling: int = Field(..., ge=0, le=100)
    technique: int = Field(..., ge=0, le=100)
    notes: str | None = Field(None, max_length=500)


class CombineScoreOut(BaseModel):
    player_id: uuid.UUID
    sport: str
    pace: int
    shooting: int
    dribbling: int
    technique: int
    overall: float
    rating_delta: float
    new_rating: float
    notes: str | None
