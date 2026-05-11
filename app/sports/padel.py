from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PadelSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class PadelGameStats(BaseModel):
    side_played: PadelSide
    games_won: int = Field(..., ge=0)
    games_lost: int = Field(..., ge=0)
    points_won: int = Field(0, ge=0)
    winners: int = Field(0, ge=0)
    unforced_errors: int = Field(0, ge=0)
    first_serve_pct: float | None = Field(None, ge=0.0, le=100.0)
    double_faults: int = Field(0, ge=0)
    smashes: int = Field(0, ge=0)

    @model_validator(mode="after")
    def validate_games_consistency(self) -> PadelGameStats:
        total = self.games_won + self.games_lost
        if total == 0:
            raise ValueError("games_won + games_lost must be > 0")
        return self
