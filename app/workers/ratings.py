from __future__ import annotations

import asyncio
import uuid

from app.workers import celery_app

# Pure helpers — no DB, no Celery.  Lives in base.py so non-worker code can
# import them without pulling in the full Celery stack.
from app.engines.rating.base import determine_match_result, opponent_avg_rating


# ---------------------------------------------------------------------------
# Public Celery tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def recalculate_match_ratings(self, match_id: str) -> dict:
    """Triggered after result quorum is reached.

    Bridges sync Celery into async SQLAlchemy via asyncio.run().
    All DB work lives in _recalculate_async to keep this function thin.
    """
    try:
        return asyncio.run(_recalculate_async(match_id))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def replay_ratings_for_algorithm(sport: str, new_algorithm_version: str) -> dict:
    """Full rating replay when the active algorithm changes.
    Replays all RatingEvents for a sport with the new engine and updates
    SportProfile.current_rating.  Heavy — run during off-peak hours only.
    """
    return {"status": "queued", "sport": sport, "new_version": new_algorithm_version}


# ---------------------------------------------------------------------------
# Async implementation  (called by the task via asyncio.run)
# ---------------------------------------------------------------------------

async def _recalculate_async(match_id_str: str) -> dict:
    # All ORM/DB imports are deferred to avoid circular-import issues at Celery
    # worker startup (the worker module is loaded before the app is fully ready).
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.core.database import AsyncSessionFactory
    from app.core.enums import MatchFormat, RatingSourceType
    from app.engines.rating import get_active_engine
    from app.engines.rating.base import RatingContext
    from app.models.match import Match, MatchRoster
    from app.models.peer_review import PeerReview
    from app.models.rating import RatingEvent
    from app.models.sport_profile import SportProfile

    match_id = uuid.UUID(match_id_str)
    engine = get_active_engine()

    async with AsyncSessionFactory() as db:
        # ── 1. Load match with rosters and per-roster game stats ──────────
        result = await db.execute(
            select(Match)
            .where(Match.id == match_id)
            .options(selectinload(Match.rosters).selectinload(MatchRoster.game_stats))
        )
        match = result.scalar_one_or_none()
        if match is None:
            return {"status": "skipped", "reason": "match not found", "match_id": match_id_str}

        if match.home_score is None or match.away_score is None:
            return {"status": "skipped", "reason": "no result submitted", "match_id": match_id_str}

        # ── 2. Idempotency guard ──────────────────────────────────────────
        # The task may be enqueued more than once (retry, duplicate confirm).
        # If RatingEvent rows already exist for this match, the work is done.
        existing_check = await db.execute(
            select(RatingEvent.id).where(RatingEvent.match_id == match_id).limit(1)
        )
        if existing_check.scalar_one_or_none() is not None:
            return {"status": "skipped", "reason": "ratings already calculated", "match_id": match_id_str}

        # ── 3. Determine active roster ────────────────────────────────────
        # attended=False means explicitly marked absent; None means unknown → include.
        active_rosters: list[MatchRoster] = [r for r in match.rosters if r.attended is not False]
        if not active_rosters:
            return {"status": "skipped", "reason": "no attending players", "match_id": match_id_str}

        player_ids = [r.player_id for r in active_rosters]
        player_team: dict[uuid.UUID, str] = {r.player_id: r.team for r in active_rosters}

        # ── 4. Load sport profiles (current ratings) ──────────────────────
        profiles_result = await db.execute(
            select(SportProfile).where(
                SportProfile.player_id.in_(player_ids),
                SportProfile.sport == match.sport,
            )
        )
        profiles: dict[uuid.UUID, SportProfile] = {
            p.player_id: p for p in profiles_result.scalars()
        }

        # ── 5. Load peer reviews for this match ───────────────────────────
        reviews_result = await db.execute(
            select(PeerReview).where(PeerReview.match_id == match_id)
        )
        reviews_by_player: dict[uuid.UUID, list[PeerReview]] = {}
        for rev in reviews_result.scalars():
            reviews_by_player.setdefault(rev.reviewed_player_id, []).append(rev)

        # ── 6. Safe enum conversion ───────────────────────────────────────
        try:
            match_format = MatchFormat(match.format)
        except ValueError:
            match_format = MatchFormat.PICKUP  # unknown format → lowest weight

        # Flat rating lookup passed into the pure helper.
        current_ratings: dict[uuid.UUID, float] = {
            pid: p.current_rating for pid, p in profiles.items()
        }

        # ── 7. Compute and APPEND RatingEvents ────────────────────────────
        new_events: list[RatingEvent] = []
        win_results: dict[uuid.UUID, str] = {}

        for roster in active_rosters:
            pid = roster.player_id
            profile = profiles.get(pid)
            if profile is None:
                # No sport profile for this player → skip; can't rate without a baseline.
                continue

            current_rating = profile.current_rating
            team = player_team[pid]
            match_result = determine_match_result(team, match.home_score, match.away_score)
            win_results[pid] = match_result

            opp_avg = opponent_avg_rating(
                pid, team, player_team, current_ratings, fallback=current_rating
            )

            # Aggregate peer score: mean of all individual sub-ratings received
            # by this player in this match across all review categories.
            peer_score: float | None = None
            player_reviews = reviews_by_player.get(pid, [])
            if player_reviews:
                all_values = [
                    v
                    for r in player_reviews
                    for v in r.ratings.values()
                    if isinstance(v, (int, float))
                ]
                if all_values:
                    peer_score = sum(all_values) / len(all_values)

            context = RatingContext(
                player_id=pid,
                sport=match.sport,
                current_rating=current_rating,
                opponent_avg_rating=opp_avg,
                match_result=match_result,
                match_format=match_format,
                game_stats=roster.game_stats.stats if roster.game_stats else {},
                peer_review_score=peer_score,
            )
            delta = engine.compute(context)  # pure — no DB access inside

            # APPEND ONLY — never UPDATE or DELETE rating_events rows.
            event = RatingEvent(
                player_id=pid,
                sport=match.sport,
                match_id=match_id,
                rating_before=current_rating,
                rating_after=delta.new_rating,
                delta=delta.delta,
                algorithm_version=delta.algorithm_version,
                source_type=RatingSourceType.MATCH_RESULT.value,
                source_id=match_id,  # non-nullable; the match is the source for this event type
                breakdown=delta.breakdown,
            )
            new_events.append(event)

        for event in new_events:
            db.add(event)

        # ── 8. Update denormalized SportProfile cache ─────────────────────
        # The event log is the source of truth; sport_profiles.current_rating is
        # a convenience cache updated here for fast leaderboard/matchmaking reads.
        for event in new_events:
            profile = profiles[event.player_id]
            profile.current_rating = event.rating_after
            profile.career_games += 1
            if win_results.get(event.player_id) == "win":
                profile.career_wins += 1

        await db.commit()

    return {
        "status": "done",
        "match_id": match_id_str,
        "players_rated": len(new_events),
        "engine": engine.version,
    }
