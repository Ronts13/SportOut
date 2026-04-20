from __future__ import annotations

import uuid

from app.adapters.filming.base import FilmingProvider, HighlightRequest, HighlightResult


class ManualUploadAdapter(FilmingProvider):
    """Fallback adapter: player uploads video manually via S3 pre-signed URL.
    No CV analysis or auto-clipping — the full uploaded video becomes the highlight."""

    async def start_session(self, match_id: uuid.UUID) -> str:
        return f"manual:{match_id}"

    async def stop_session(self, provider_session_id: str) -> str:
        # Manual uploads have no stop event; footage URL is set by the upload endpoint directly.
        return ""

    async def generate_highlights(self, request: HighlightRequest) -> list[HighlightResult]:
        return [
            HighlightResult(
                player_id=request.player_id,
                url=request.raw_footage_url,
                thumbnail_url=None,
                duration_seconds=request.duration_seconds,
                event_tags=[],
            )
        ]

    async def extract_video_metrics(self, raw_footage_url: str) -> dict:
        return {}
