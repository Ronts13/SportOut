from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, computed_field, model_validator


class BasketballPosition(str, Enum):
    POINT_GUARD = "pg"
    SHOOTING_GUARD = "sg"
    SMALL_FORWARD = "sf"
    POWER_FORWARD = "pf"
    CENTER = "c"


class BasketballGameStats(BaseModel):
    position_played: BasketballPosition
    minutes_played: int = Field(..., ge=0, le=60)
    points: int = Field(0, ge=0)
    assists: int = Field(0, ge=0)
    rebounds_offensive: int = Field(0, ge=0)
    rebounds_defensive: int = Field(0, ge=0)
    steals: int = Field(0, ge=0)
    blocks: int = Field(0, ge=0)
    turnovers: int = Field(0, ge=0)
    field_goals_made: int = Field(0, ge=0)
    field_goal_attempts: int = Field(0, ge=0)
    three_points_made: int = Field(0, ge=0)
    three_point_attempts: int = Field(0, ge=0)
    free_throws_made: int = Field(0, ge=0)
    free_throw_attempts: int = Field(0, ge=0)
    plus_minus: int = 0

    @computed_field
    @property
    def rebounds_total(self) -> int:
        return self.rebounds_offensive + self.rebounds_defensive

    @model_validator(mode="after")
    def validate_shot_consistency(self) -> BasketballGameStats:
        if self.field_goals_made > self.field_goal_attempts:
            raise ValueError("field_goals_made cannot exceed field_goal_attempts")
        if self.three_points_made > self.three_point_attempts:
            raise ValueError("three_points_made cannot exceed three_point_attempts")
        if self.three_points_made > self.field_goals_made:
            raise ValueError("three_points_made cannot exceed field_goals_made")
        if self.free_throws_made > self.free_throw_attempts:
            raise ValueError("free_throws_made cannot exceed free_throw_attempts")
        return self
