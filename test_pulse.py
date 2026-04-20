"""
SportOut Pulse Check — validates schemas and sport stat registry are wired correctly.
Run from repo root: python test_pulse.py
"""

import json
import uuid
from datetime import date, datetime, timezone

# ── Schemas ──────────────────────────────────────────────────────────────────
from app.schemas.player import PlayerCardOut, PlayerProfileOut
from app.schemas.rating import RatingEventOut, RatingHistoryOut

# ── Sport stat registry ───────────────────────────────────────────────────────
from app.sports.registry import validate_game_stats
from app.core.enums import Sport, MatchFormat

# ── Rating engine ─────────────────────────────────────────────────────────────
from app.engines.rating import get_active_engine
from app.engines.rating.base import RatingContext


def section(title: str) -> None:
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print('-' * 60)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Player profile (Instagram-style card)
# ─────────────────────────────────────────────────────────────────────────────
section("1 · Player Profile Card")

player_id = uuid.uuid4()
now = datetime.now(timezone.utc)

profile_data = {
    "id": player_id,
    "display_name": "Lior Ben-David",
    "username": "lior_bd10",
    "avatar_url": "https://cdn.sportout.gg/avatars/lior_bd10.jpg",
    "banner_url": "https://cdn.sportout.gg/banners/lior_bd10.jpg",
    "city": "Tel Aviv",
    "bio": "Soccer midfielder. Always looking for the next pickup game ⚽",
    "date_of_birth": date(2000, 3, 15),
    "card_is_public": True,
    "follower_count": 142,
    "following_count": 87,
    "created_at": now,
}

profile = PlayerProfileOut(**profile_data)
print(json.dumps(json.loads(profile.model_dump_json()), indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# 2. Soccer stat schema — valid payload
# ─────────────────────────────────────────────────────────────────────────────
section("2 · Soccer GameStats — valid payload")

soccer_raw = {
    "position_played": "cm",
    "minutes_played": 90,
    "goals": 2,
    "assists": 1,
    "shots_on_target": 3,
    "shots_total": 5,
    "pass_accuracy_pct": 82.5,
    "distance_covered_km": 9.4,
    "yellow_cards": 0,
    "red_cards": 0,
}

soccer_stats = validate_game_stats(Sport.SOCCER, soccer_raw)
print(json.dumps(json.loads(soccer_stats.model_dump_json()), indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Basketball stat schema — valid payload with computed rebounds_total
# ─────────────────────────────────────────────────────────────────────────────
section("3 · Basketball GameStats — valid payload (computed rebounds_total)")

basketball_raw = {
    "position_played": "pg",
    "minutes_played": 32,
    "points": 18,
    "field_goals_made": 6,
    "field_goal_attempts": 14,
    "three_points_made": 2,
    "three_point_attempts": 5,
    "free_throws_made": 4,
    "free_throw_attempts": 4,
    "rebounds_offensive": 2,
    "rebounds_defensive": 5,
    "assists": 7,
    "steals": 2,
    "blocks": 0,
    "turnovers": 3,
    "fouls": 2,
    "plus_minus": 12,
}

basketball_stats = validate_game_stats(Sport.BASKETBALL, basketball_raw)
print(json.dumps(json.loads(basketball_stats.model_dump_json()), indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Schema validation guard — shots_on_target > shots_total should raise
# ─────────────────────────────────────────────────────────────────────────────
section("4 · Schema Guard — shots_on_target > shots_total (expect ValueError)")

try:
    validate_game_stats(Sport.SOCCER, {**soccer_raw, "shots_on_target": 10, "shots_total": 3})
    print("  ERROR: validation should have raised!")
except ValueError as exc:
    print(f"  Correctly rejected: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Elo rating engine — compute a rating delta
# ─────────────────────────────────────────────────────────────────────────────
section("5 · Elo Rating Engine — compute delta for a win")

engine = get_active_engine()
print(f"  Active engine: {engine.version}")

context = RatingContext(
    player_id=player_id,
    sport=Sport.SOCCER,
    current_rating=1050.0,
    opponent_avg_rating=980.0,
    match_result="win",
    match_format=MatchFormat.SCRIMMAGE,
    peer_review_score=4.2,
)

delta = engine.compute(context)
print(json.dumps({
    "engine": delta.algorithm_version,
    "rating_before": context.current_rating,
    "delta": delta.delta,
    "rating_after": delta.new_rating,
    "breakdown": delta.breakdown,
}, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# 6. RatingHistoryOut schema (drives the profile trend chart)
# ─────────────────────────────────────────────────────────────────────────────
section("6 · RatingHistoryOut — trend chart payload")

event = RatingEventOut(
    id=uuid.uuid4(),
    player_id=player_id,
    sport="soccer",
    match_id=uuid.uuid4(),
    rating_before=context.current_rating,
    rating_after=delta.new_rating,
    delta=delta.delta,
    algorithm_version=delta.algorithm_version,
    source_type="match_result",
    breakdown=delta.breakdown,
    created_at=now,
)

history = RatingHistoryOut(
    sport="soccer",
    current_rating=delta.new_rating,
    events=[event],
)
print(json.dumps(json.loads(history.model_dump_json()), indent=2))


# ─────────────────────────────────────────────────────────────────────────────
print("\n[OK]  All pulse checks passed.\n")
