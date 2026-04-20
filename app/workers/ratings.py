from __future__ import annotations

from app.workers import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def recalculate_match_ratings(self, match_id: str) -> dict:
    """Post-game rating recalculation triggered after result quorum is reached:
    1. Load Match + MatchRosters + PlayerGameStats
    2. Build a RatingContext for each attending player
    3. Call get_active_engine().compute(context) — pure, no DB access
    4. Append RatingEvent rows (never update existing ones)
    5. Update denormalized SportProfile.current_rating
    """
    try:
        from app.engines.rating import get_active_engine

        engine = get_active_engine()
        # Service layer implementation in next sprint
        return {"status": "queued", "match_id": match_id, "engine": engine.version}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def replay_ratings_for_algorithm(sport: str, new_algorithm_version: str) -> dict:
    """Full rating replay when the active algorithm changes.
    Replays all RatingEvents for a sport with the new engine and updates SportProfile.current_rating.
    Heavy operation — run during off-peak hours only.
    """
    return {"status": "queued", "sport": sport, "new_version": new_algorithm_version}
