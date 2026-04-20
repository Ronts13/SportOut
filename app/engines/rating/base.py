from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.enums import MatchFormat, Sport


@dataclass
class RatingContext:
    player_id: uuid.UUID
    sport: Sport
    current_rating: float
    opponent_avg_rating: float
    match_result: str           # "win" | "loss" | "draw"
    match_format: MatchFormat
    game_stats: dict = field(default_factory=dict)
    peer_review_score: float | None = None
    video_metrics: dict | None = None


@dataclass
class RatingDelta:
    delta: float
    new_rating: float
    algorithm_version: str
    breakdown: dict = field(default_factory=dict)


class RatingEngine(ABC):
    @abstractmethod
    def compute(self, context: RatingContext) -> RatingDelta:
        """Compute a rating delta from a full match context.
        Must be pure — no database access, no side effects."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Unique version string written to every RatingEvent row for audit and algorithm replay."""
        ...
