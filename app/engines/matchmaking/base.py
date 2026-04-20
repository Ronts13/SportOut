from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.enums import Sport


@dataclass
class MatchmakingQuery:
    player_id: uuid.UUID
    sport: Sport
    player_rating: float
    latitude: float
    longitude: float
    radius_km: float = 10.0
    rating_tolerance: float = 200.0  # ± range around player_rating


@dataclass
class MatchSuggestion:
    match_id: uuid.UUID
    score: float                 # composite 0–1 — higher is better fit
    skill_compatibility: float
    distance_km: float
    play_history_bonus: float    # boost if player has played with roster members before


class MatchmakingEngine(ABC):
    @abstractmethod
    async def suggest_matches(self, query: MatchmakingQuery) -> list[MatchSuggestion]:
        """Return open matches ranked by composite compatibility score for the querying player."""
        ...
