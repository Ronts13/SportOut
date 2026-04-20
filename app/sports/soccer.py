from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SoccerPosition(str, Enum):
    GOALKEEPER = "gk"
    CENTRE_BACK = "cb"
    FULL_BACK = "fb"
    MIDFIELDER = "cm"
    WINGER = "wg"
    STRIKER = "st"


class SoccerGameStats(BaseModel):
    position_played: SoccerPosition
    minutes_played: int = Field(..., ge=0, le=120)
    goals: int = Field(0, ge=0)
    assists: int = Field(0, ge=0)
    shots_total: int = Field(0, ge=0)
    shots_on_target: int = Field(0, ge=0)
    pass_accuracy_pct: float | None = Field(None, ge=0.0, le=100.0)
    distance_covered_km: float | None = Field(None, ge=0.0)
    yellow_cards: int = Field(0, ge=0, le=2)
    red_cards: int = Field(0, ge=0, le=1)

    @model_validator(mode="after")
    def validate_shot_consistency(self) -> SoccerGameStats:
        if self.shots_on_target > self.shots_total:
            raise ValueError("shots_on_target cannot exceed shots_total")
        return self
