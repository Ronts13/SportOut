from __future__ import annotations

from app.workers import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_media_session(self, media_session_id: str) -> dict:
    """Full async video pipeline for a completed match:
    1. Fetch MediaSession + rostered players from DB
    2. Call FilmingProvider.generate_highlights() for each player
    3. Persist Highlight rows
    4. Call FilmingProvider.extract_video_metrics()
    5. Update MediaSession.video_metrics + processing_status
    6. Enqueue recalculate_match_ratings if video metrics are available
    """
    try:
        from app.adapters.filming import get_provider
        from app.core.config import settings

        provider = get_provider(settings.FILMING_PROVIDER)
        # Service layer implementation in next sprint
        return {"status": "queued", "media_session_id": media_session_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_player_highlight(self, media_session_id: str, player_id: str) -> dict:
    """Generate a single player's highlight clip. Can be enqueued per-player for parallelism."""
    try:
        return {"status": "queued", "player_id": player_id, "media_session_id": media_session_id}
    except Exception as exc:
        raise self.retry(exc=exc)
