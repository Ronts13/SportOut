from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.media import HighlightOut
from app.schemas.player import (
    LeaderboardEntryOut,
    PlayerCardOut,
    PlayerCreate,
    PlayerProfileOut,
    PlayerUpdate,
)
from app.schemas.rating import PeerReviewCreate, PeerReviewOut, RatingHistoryOut

router = APIRouter(prefix="/players", tags=["players"])

# ---------------------------------------------------------------------------
# Mock data — mirrors the frontend Rankings tab
# ---------------------------------------------------------------------------
_MOCK_LEADERBOARD: list[LeaderboardEntryOut] = [
    LeaderboardEntryOut(
        rank=1,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        display_name="Ron",
        sport="padel",
        current_rating=9.4,
        wins=38,
        losses=4,
    ),
    LeaderboardEntryOut(
        rank=2,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        display_name="Kobi Bar",
        sport="padel",
        current_rating=8.9,
        wins=31,
        losses=7,
    ),
    LeaderboardEntryOut(
        rank=3,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        display_name="Lior Khaytov",
        sport="padel",
        current_rating=8.0,
        wins=28,
        losses=10,
    ),
    LeaderboardEntryOut(
        rank=4,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000004"),
        display_name="Liran Malki",
        sport="padel",
        current_rating=7.4,
        wins=22,
        losses=12,
    ),
    LeaderboardEntryOut(
        rank=5,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000005"),
        display_name="Ofir Tuti",
        sport="padel",
        current_rating=6.8,
        wins=18,
        losses=14,
    ),
    LeaderboardEntryOut(
        rank=6,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000006"),
        display_name="Dan Haim Lee",
        sport="tennis",
        current_rating=6.3,
        wins=15,
        losses=16,
    ),
    LeaderboardEntryOut(
        rank=7,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000007"),
        display_name="Ron Tsemakhman",
        sport="padel",
        current_rating=5.9,
        wins=12,
        losses=18,
    ),
    LeaderboardEntryOut(
        rank=8,
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000008"),
        display_name="Aviram Shuster",
        sport="tennis",
        current_rating=5.5,
        wins=9,
        losses=20,
    ),
]

# ---------------------------------------------------------------------------
# Player profile registry — keyed by player_id UUID.
# Derived from _MOCK_LEADERBOARD so names, sports, and ratings stay in sync.
# PlayerProfileOut has no rating/sport fields; both are surfaced via bio.
# ---------------------------------------------------------------------------
_CREATED_AT = datetime(2024, 1, 1, 0, 0, 0)

_MOCK_PROFILES: dict[uuid.UUID, PlayerProfileOut] = {
    e.player_id: PlayerProfileOut(
        id=e.player_id,
        display_name=e.display_name,
        # username: lowercase display_name, spaces replaced with underscores
        username=e.display_name.lower().replace(" ", "_"),
        avatar_url=None,
        banner_url=None,
        city="Tel Aviv",
        bio=f"{e.sport.capitalize()} player · Rating {e.current_rating} · {e.wins}W {e.losses}L",
        date_of_birth=None,
        card_is_public=True,
        follower_count=(50 - e.rank * 4),   # higher rank → more followers
        following_count=10,
        created_at=_CREATED_AT,
    )
    for e in _MOCK_LEADERBOARD
}


@router.post("/", response_model=PlayerProfileOut, status_code=status.HTTP_201_CREATED)
async def register_player(payload: PlayerCreate, db: AsyncSession = Depends(get_db)) -> PlayerProfileOut:
    raise NotImplementedError


# NOTE: must be defined BEFORE /{player_id} so FastAPI doesn't match
# the literal string "leaderboard" as a UUID path parameter.
@router.get("/leaderboard/{sport}", response_model=list[LeaderboardEntryOut])
async def get_leaderboard(
    sport: str,
    city: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[LeaderboardEntryOut]:
    """Mock: returns hardcoded leaderboard. Real impl will query ratings table."""
    results = [e for e in _MOCK_LEADERBOARD if e.sport == sport]
    return results[:limit]


@router.get("/{player_id}", response_model=PlayerProfileOut)
async def get_player(player_id: uuid.UUID) -> PlayerProfileOut:
    """Mock: returns a player's full profile from the in-memory registry."""
    profile = _MOCK_PROFILES.get(player_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return profile


@router.patch("/{player_id}", response_model=PlayerProfileOut)
async def update_player(
    player_id: uuid.UUID,
    payload: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
) -> PlayerProfileOut:
    raise NotImplementedError


@router.get("/{player_id}/rating/{sport}", response_model=RatingHistoryOut)
async def get_rating_history(
    player_id: uuid.UUID,
    sport: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> RatingHistoryOut:
    raise NotImplementedError


@router.get("/{player_id}/highlights", response_model=list[HighlightOut])
async def get_player_highlights(
    player_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[HighlightOut]:
    raise NotImplementedError


@router.post("/{player_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def follow_player(player_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError


@router.delete("/{player_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_player(player_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError


@router.post("/reviews", response_model=PeerReviewOut, status_code=status.HTTP_201_CREATED)
async def submit_peer_review(
    payload: PeerReviewCreate,
    db: AsyncSession = Depends(get_db),
) -> PeerReviewOut:
    raise NotImplementedError


@router.post("/reviews/{review_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_peer_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError
