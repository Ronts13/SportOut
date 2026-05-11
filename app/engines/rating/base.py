from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.enums import MatchFormat, Sport


# ---------------------------------------------------------------------------
# Pure rating helpers — no DB access, no side effects.
# Used by the rating worker and exposed here so non-Celery code can import
# them without pulling in the full worker module.
# ---------------------------------------------------------------------------

def determine_match_result(team: str, home_score: int, away_score: int) -> str:
    """Return 'win', 'loss', or 'draw' from the perspective of a player on *team*."""
    if team == "home":
        if home_score > away_score:
            return "win"
        if home_score < away_score:
            return "loss"
        return "draw"
    if team == "away":
        if away_score > home_score:
            return "win"
        if away_score < home_score:
            return "loss"
        return "draw"
    # "none" team (pickup / unassigned) — treated as a draw for rating purposes.
    return "draw"


def opponent_avg_rating(
    player_id: uuid.UUID,
    team: str,
    player_team: dict[uuid.UUID, str],
    current_ratings: dict[uuid.UUID, float],
    fallback: float,
) -> float:
    """Return the mean rating of the player's opponents.

    For "home"/"away" teams, opponents are the other team.
    For "none" (pickup), everyone else is an opponent.
    Returns *fallback* when no opponent ratings are available.
    """
    if team in ("home", "away"):
        opponent_team = "away" if team == "home" else "home"
        ratings = [
            current_ratings[opid]
            for opid, t in player_team.items()
            if t == opponent_team and opid in current_ratings
        ]
    else:
        ratings = [
            current_ratings[opid]
            for opid in player_team
            if opid != player_id and opid in current_ratings
        ]
    return sum(ratings) / len(ratings) if ratings else fallback


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
