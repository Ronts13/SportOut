from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class HighlightRequest:
    media_session_id: uuid.UUID
    player_id: uuid.UUID
    raw_footage_url: str
    duration_seconds: int = 60


@dataclass
class HighlightResult:
    player_id: uuid.UUID
    url: str
    thumbnail_url: str | None
    duration_seconds: int
    event_tags: list[str] = field(default_factory=list)


class FilmingProvider(ABC):
    @abstractmethod
    async def start_session(self, match_id: uuid.UUID) -> str:
        """Notify the provider that recording has started. Returns a provider-scoped session ID."""
        ...

    @abstractmethod
    async def stop_session(self, provider_session_id: str) -> str:
        """Signal end of recording. Returns the raw footage URL when ready."""
        ...

    @abstractmethod
    async def generate_highlights(self, request: HighlightRequest) -> list[HighlightResult]:
        """Generate per-player highlight clips from a completed recording."""
        ...

    @abstractmethod
    async def extract_video_metrics(self, raw_footage_url: str) -> dict:
        """Run CV analysis and return structured metrics consumable by the RatingEngine."""
        ...
