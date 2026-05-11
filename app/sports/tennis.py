from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class TennisGameStats(BaseModel):
    games_won: int = Field(..., ge=0)
    games_lost: int = Field(..., ge=0)
    sets_won: int = Field(..., ge=0)
    sets_lost: int = Field(..., ge=0)
    aces: int = Field(0, ge=0)
    double_faults: int = Field(0, ge=0)
    first_serve_pct: float | None = Field(None, ge=0.0, le=100.0)
    winners: int = Field(0, ge=0)
    unforced_errors: int = Field(0, ge=0)
    max_serve_speed_kmh: float | None = Field(None, ge=0.0, le=300.0)

    @model_validator(mode="after")
    def validate_sets_consistency(self) -> TennisGameStats:
        if self.sets_won + self.sets_lost == 0:
            raise ValueError("sets_won + sets_lost must be > 0")
        return self
