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
# 7. MatchCreate — rating bracket validation
# ─────────────────────────────────────────────────────────────────────────────
section("7 · MatchCreate — rating bracket validation")

from app.schemas.match import MatchCreate

valid_match = MatchCreate(
    sport="padel",
    scheduled_at=datetime.now(timezone.utc),
    min_rating=800.0,
    max_rating=1200.0,
    max_players=4,
)
print(f"  Valid bracket: min={valid_match.min_rating}, max={valid_match.max_rating} [OK]")

try:
    MatchCreate(
        sport="padel",
        scheduled_at=datetime.now(timezone.utc),
        min_rating=1200.0,
        max_rating=800.0,
    )
    print("  ERROR: inverted bracket should have raised!")
except ValueError as exc:
    print(f"  Correctly rejected inverted bracket: {exc}")

no_bracket = MatchCreate(sport="tennis", scheduled_at=datetime.now(timezone.utc))
assert no_bracket.min_rating is None and no_bracket.max_rating is None
print("  No-bracket match (open to all ratings) [OK]")


# ─────────────────────────────────────────────────────────────────────────────
# 8. PostGIS proximity SQL — statement structure smoke test (no DB needed)
# ─────────────────────────────────────────────────────────────────────────────
section("8 · PostGIS proximity SQL — statement structure smoke test")

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.dialects import postgresql

from app.models.facility import Facility
from app.models.match import Match

TEL_AVIV_LAT, TEL_AVIV_LON, RADIUS_KM = 32.0853, 34.7818, 5.0

caller_point = cast(
    func.ST_SetSRID(func.ST_MakePoint(TEL_AVIV_LON, TEL_AVIV_LAT), 4326),
    Geography,
)

stmt = (
    select(Match)
    .join(Facility, Match.facility_id == Facility.id)
    .where(
        Match.status == "open",
        Match.is_private.is_(False),
        func.ST_DWithin(cast(Facility.location, Geography), caller_point, RADIUS_KM * 1000),
    )
    .order_by(Match.scheduled_at)
    .limit(20)
)

sql_str = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))

assert "ST_DWithin" in sql_str, "ST_DWithin missing from compiled SQL"
assert "ST_MakePoint" in sql_str, "ST_MakePoint missing from compiled SQL"
assert "ST_SetSRID" in sql_str, "ST_SetSRID missing from compiled SQL"

# Confirm the geography cast is present (ensures meter-based accuracy per CLAUDE.md rule)
assert "geography" in sql_str.lower(), "geography cast missing from compiled SQL"

excerpt_start = sql_str.lower().find("st_dwithin")
print(f"  ST_DWithin  : YES")
print(f"  ST_MakePoint: YES")
print(f"  Geography cast: YES")
print(f"  SQL excerpt : ...{sql_str[excerpt_start:excerpt_start + 100]}...")


# ─────────────────────────────────────────────────────────────────────────────
# 9. PeerReviewCreate — score validation
# ─────────────────────────────────────────────────────────────────────────────
section("9 · PeerReviewCreate — score boundary validation")

from app.schemas.rating import PeerReviewCreate

match_id_pr = uuid.uuid4()
reviewed_id = uuid.uuid4()

valid_review = PeerReviewCreate(
    reviewed_player_id=reviewed_id,
    match_id=match_id_pr,
    ratings={"defending": 4, "attacking": 3, "teamwork": 5, "effort": 2},
)
assert all(1 <= v <= 5 for v in valid_review.ratings.values())
print(f"  Valid review ratings: {valid_review.ratings} [OK]")

# Out-of-range score should raise
try:
    PeerReviewCreate(
        reviewed_player_id=reviewed_id,
        match_id=match_id_pr,
        ratings={"effort": 6},
    )
    print("  ERROR: should have raised for score=6!")
except ValueError as exc:
    print(f"  Correctly rejected score=6: {exc}")

try:
    PeerReviewCreate(
        reviewed_player_id=reviewed_id,
        match_id=match_id_pr,
        ratings={"effort": 0},
    )
    print("  ERROR: should have raised for score=0!")
except ValueError as exc:
    print(f"  Correctly rejected score=0: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 10. _determine_result helper — all team/score combinations
# ─────────────────────────────────────────────────────────────────────────────
section("10 · _determine_result — win / loss / draw for all team slots")

from app.engines.rating.base import determine_match_result as _determine_result

cases = [
    ("home", 3, 1, "win"),
    ("home", 1, 3, "loss"),
    ("home", 2, 2, "draw"),
    ("away", 1, 3, "win"),
    ("away", 3, 1, "loss"),
    ("away", 2, 2, "draw"),
    ("none", 5, 0, "draw"),   # unassigned team is always draw
]
for team, hs, as_, expected in cases:
    got = _determine_result(team, hs, as_)
    assert got == expected, f"team={team} {hs}-{as_}: expected {expected}, got {got}"
    print(f"  team={team:4s}  {hs}-{as_}  -> {got} [OK]")


# ─────────────────────────────────────────────────────────────────────────────
# 11. _opponent_ratings helper — team and pickup cases
# ─────────────────────────────────────────────────────────────────────────────
section("11 · opponent_avg_rating — team vs pickup aggregation")

from app.engines.rating.base import opponent_avg_rating

p1, p2, p3, p4 = (uuid.uuid4() for _ in range(4))

team_map = {p1: "home", p2: "home", p3: "away", p4: "away"}
# opponent_avg_rating takes a flat {player_id: float} dict
rating_map = {p1: 1000.0, p2: 1100.0, p3: 900.0, p4: 950.0}

# Home player → mean of away ratings
opp = opponent_avg_rating(p1, "home", team_map, rating_map, fallback=0.0)
assert opp == (900.0 + 950.0) / 2, f"Expected 925.0, got {opp}"
print(f"  Home player opponent avg = {opp} (mean of away ratings) [OK]")

# Away player → mean of home ratings
opp2 = opponent_avg_rating(p3, "away", team_map, rating_map, fallback=0.0)
assert opp2 == (1000.0 + 1100.0) / 2, f"Expected 1050.0, got {opp2}"
print(f"  Away player opponent avg = {opp2} (mean of home ratings) [OK]")

# Pickup ("none") → mean of everyone else
pickup_map = {p1: "none", p2: "none", p3: "none"}
pickup_ratings = {p1: 1000.0, p2: 1100.0, p3: 900.0}
opp3 = opponent_avg_rating(p1, "none", pickup_map, pickup_ratings, fallback=0.0)
assert opp3 == (1100.0 + 900.0) / 2, f"Expected 1000.0, got {opp3}"
print(f"  Pickup player opponent avg = {opp3} (mean of all others) [OK]")


# ─────────────────────────────────────────────────────────────────────────────
# 12. End-to-end rating computation — single match, two teams
# ─────────────────────────────────────────────────────────────────────────────
section("12 · End-to-end Trust Engine simulation (no DB)")

from app.engines.rating import get_active_engine
from app.engines.rating.base import RatingContext
from app.core.enums import MatchFormat, Sport

eng = get_active_engine()

home_pid, away_pid = uuid.uuid4(), uuid.uuid4()
home_rating, away_rating = 1050.0, 980.0

# Home team wins 3-1; home player has a peer review of 4.5
home_ctx = RatingContext(
    player_id=home_pid,
    sport=Sport.SOCCER,
    current_rating=home_rating,
    opponent_avg_rating=away_rating,
    match_result=_determine_result("home", 3, 1),
    match_format=MatchFormat.PICKUP,
    peer_review_score=4.5,
)
away_ctx = RatingContext(
    player_id=away_pid,
    sport=Sport.SOCCER,
    current_rating=away_rating,
    opponent_avg_rating=home_rating,
    match_result=_determine_result("away", 3, 1),
    match_format=MatchFormat.PICKUP,
    peer_review_score=None,
)

home_delta = eng.compute(home_ctx)
away_delta = eng.compute(away_ctx)

# Winner must gain, loser must lose.
assert home_delta.delta > 0, f"Home winner should gain rating, got delta={home_delta.delta}"
assert away_delta.delta < 0, f"Away loser should lose rating, got delta={away_delta.delta}"
# Ratings must never go negative.
assert home_delta.new_rating >= 0
assert away_delta.new_rating >= 0

print(f"  Home winner: {home_rating:.1f} -> {home_delta.new_rating:.4f} (delta {home_delta.delta:+.4f}) [OK]")
print(f"  Away loser:  {away_rating:.1f} -> {away_delta.new_rating:.4f} (delta {away_delta.delta:+.4f}) [OK]")
print(f"  Algorithm version recorded: {home_delta.algorithm_version}")


# ─────────────────────────────────────────────────────────────────────────────
print("\n[OK]  All pulse checks passed.\n")
