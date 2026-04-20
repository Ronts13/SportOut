from __future__ import annotations

import uuid

from app.adapters.filming.base import FilmingProvider, HighlightRequest, HighlightResult


class PixellotAdapter(FilmingProvider):
    """Pixellot AI auto-filming adapter.
    Requires PIXELLOT_API_KEY env var. Blocked on API access approval (OQ-02)."""

    async def start_session(self, match_id: uuid.UUID) -> str:
        raise NotImplementedError("Pixellot integration pending API access approval — see OQ-02")

    async def stop_session(self, provider_session_id: str) -> str:
        raise NotImplementedError("Pixellot integration pending API access approval — see OQ-02")

    async def generate_highlights(self, request: HighlightRequest) -> list[HighlightResult]:
        raise NotImplementedError("Pixellot integration pending API access approval — see OQ-02")

    async def extract_video_metrics(self, raw_footage_url: str) -> dict:
        raise NotImplementedError("Pixellot integration pending API access approval — see OQ-02")
