from __future__ import annotations

import traceback
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import TokenData, get_current_admin, get_current_user
from app.core.database import get_db
from app.core.enums import RatingSourceType, UserRole
from app.core.security import hash_password
from app.models.match import Match, MatchRoster
from app.models.peer_review import PeerReview
from app.models.player import Player, PlayerFollow
from app.models.rating import RatingEvent
from app.models.sport_profile import SportProfile
from app.models.user import User
from app.schemas.media import HighlightOut
from app.schemas.player import (
    LeaderboardEntryOut,
    PlayerCardOut,
    PlayerCreate,
    PlayerProfileOut,
    PlayerUpdate,
)
from app.schemas.rating import (
    CombineScoreCreate,
    CombineScoreOut,
    PeerReviewCreate,
    PeerReviewOut,
    RatingHistoryOut,
)

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
    print("DEBUG: Inside register_player route", flush=True)
    try:
        email_exists = await db.execute(select(User).where(User.email == payload.email))
        if email_exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        username_exists = await db.execute(select(Player).where(Player.username == payload.username))
        if username_exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

        shared_id = uuid.uuid4()
        user = User(
            id=shared_id,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=UserRole.PLAYER.value,
        )
        player = Player(
            id=shared_id,
            display_name=payload.display_name,
            username=payload.username,
            date_of_birth=payload.date_of_birth,
            city=payload.city,
        )
        db.add(user)
        db.add(player)
        print("DEBUG: About to flush to DB", flush=True)
        await db.flush()

        db.add(SportProfile(
            player_id=shared_id,
            sport="soccer",
            current_rating=1000.0,
            career_wins=0,
            career_games=0,
            is_public=True,
        ))
        await db.commit()
        print("DEBUG: Player + Soccer SportProfile created OK", flush=True)
        await db.refresh(player)
        return PlayerProfileOut.model_validate(player)
    except HTTPException:
        raise
    except Exception:
        tb_text = traceback.format_exc()
        print(f"REGISTER CRASH:\n{tb_text}", flush=True)
        raise HTTPException(status_code=500, detail=tb_text)


# NOTE: must be defined BEFORE /{player_id} so FastAPI doesn't match
# the literal string "leaderboard" as a UUID path parameter.
@router.get("/leaderboard/{sport}", response_model=list[LeaderboardEntryOut])
async def get_leaderboard(
    sport: str,
    city: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[LeaderboardEntryOut]:
    stmt = (
        select(SportProfile, Player.display_name)
        .join(Player, SportProfile.player_id == Player.id)
        .where(SportProfile.sport == sport, SportProfile.is_public.is_(True))
    )
    if city:
        stmt = stmt.where(Player.city.ilike(city))
    stmt = stmt.order_by(SportProfile.current_rating.desc()).limit(limit)

    rows = await db.execute(stmt)
    result: list[LeaderboardEntryOut] = []
    for rank, (sp, display_name) in enumerate(rows.all(), start=1):
        result.append(
            LeaderboardEntryOut(
                rank=rank,
                player_id=sp.player_id,
                display_name=display_name,
                sport=sp.sport,
                current_rating=sp.current_rating,
                wins=sp.career_wins,
                losses=max(0, sp.career_games - sp.career_wins),
            )
        )
    return result


# NOTE: /count and /me must stay ABOVE /{player_id} so FastAPI matches literals first.

@router.get("/count")
async def get_player_count(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(func.count()).select_from(Player))
    total = result.scalar_one()
    return {"total_players": total}


@router.get("/", response_model=list[PlayerProfileOut])
async def list_players(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[PlayerProfileOut]:
    result = await db.execute(select(Player).order_by(Player.created_at.desc()).limit(limit))
    return [PlayerProfileOut.model_validate(p) for p in result.scalars().all()]


@router.get("/me", response_model=PlayerProfileOut)
async def get_my_profile(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlayerProfileOut:
    player = await db.get(Player, uuid.UUID(current_user.user_id))
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player profile not found")
    return PlayerProfileOut.model_validate(player)


@router.patch("/me", response_model=PlayerProfileOut)
async def update_my_profile(
    payload: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> PlayerProfileOut:
    player = await db.get(Player, uuid.UUID(current_user.user_id))
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(player, field, value)
    await db.flush()
    await db.refresh(player)
    return PlayerProfileOut.model_validate(player)


@router.get("/{player_id}", response_model=PlayerProfileOut)
async def get_player(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PlayerProfileOut:
    player = await db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return PlayerProfileOut.model_validate(player)


@router.patch("/{player_id}", response_model=PlayerProfileOut)
async def update_player(
    player_id: uuid.UUID,
    payload: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> PlayerProfileOut:
    if str(player_id) != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another player's profile")
    player = await db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(player, field, value)
    await db.flush()
    await db.refresh(player)
    return PlayerProfileOut.model_validate(player)


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


@router.post("/{player_id}/follow", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def follow_player(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> None:
    follower_id = uuid.UUID(current_user.user_id)
    if follower_id == player_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
    target = await db.get(Player, player_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    existing = await db.execute(
        select(PlayerFollow).where(
            PlayerFollow.follower_id == follower_id,
            PlayerFollow.followed_id == player_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return  # Idempotent — already following
    db.add(PlayerFollow(follower_id=follower_id, followed_id=player_id))
    follower_player = await db.get(Player, follower_id)
    if follower_player:
        follower_player.following_count += 1
    target.follower_count += 1
    await db.flush()


@router.delete("/{player_id}/follow", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def unfollow_player(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> None:
    follower_id = uuid.UUID(current_user.user_id)
    result = await db.execute(
        select(PlayerFollow).where(
            PlayerFollow.follower_id == follower_id,
            PlayerFollow.followed_id == player_id,
        )
    )
    follow = result.scalar_one_or_none()
    if follow is None:
        return  # Already not following — idempotent
    await db.delete(follow)
    follower_player = await db.get(Player, follower_id)
    if follower_player and follower_player.following_count > 0:
        follower_player.following_count -= 1
    target = await db.get(Player, player_id)
    if target and target.follower_count > 0:
        target.follower_count -= 1
    await db.flush()


@router.get("/{player_id}/is_following")
async def check_is_following(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    follower_id = uuid.UUID(current_user.user_id)
    result = await db.execute(
        select(PlayerFollow).where(
            PlayerFollow.follower_id == follower_id,
            PlayerFollow.followed_id == player_id,
        )
    )
    return {"is_following": result.scalar_one_or_none() is not None}


@router.post("/reviews", response_model=PeerReviewOut, status_code=status.HTTP_201_CREATED)
async def submit_peer_review(
    payload: PeerReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> PeerReviewOut:
    reviewer_id = uuid.UUID(current_user.user_id)

    if reviewer_id == payload.reviewed_player_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot review yourself")

    # Verify the match exists.
    match = await db.get(Match, payload.match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    # Verify both players were rostered for this match.
    roster_rows = await db.execute(
        select(MatchRoster.player_id).where(MatchRoster.match_id == payload.match_id)
    )
    rostered: set[uuid.UUID] = set(roster_rows.scalars())

    if reviewer_id not in rostered:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You were not rostered in this match",
        )
    if payload.reviewed_player_id not in rostered:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reviewed player was not rostered in this match",
        )

    # Duplicate guard — DB unique constraint is the hard stop, but give a friendly error first.
    existing = await db.execute(
        select(PeerReview).where(
            PeerReview.reviewer_id == reviewer_id,
            PeerReview.reviewed_player_id == payload.reviewed_player_id,
            PeerReview.match_id == payload.match_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review already submitted for this player in this match",
        )

    review = PeerReview(
        reviewer_id=reviewer_id,
        reviewed_player_id=payload.reviewed_player_id,
        match_id=payload.match_id,
        ratings=payload.ratings,
        is_confirmed=False,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return PeerReviewOut.model_validate(review)


@router.post("/reviews/{review_id}/confirm", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def confirm_peer_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Admin — AI Combine manual scoring
# ---------------------------------------------------------------------------

@router.post(
    "/{player_id}/combine",
    response_model=CombineScoreOut,
    status_code=status.HTTP_201_CREATED,
    tags=["admin"],
)
async def record_combine_score(
    player_id: uuid.UUID,
    payload: CombineScoreCreate,
    db: AsyncSession = Depends(get_db),
    _admin: TokenData = Depends(get_current_admin),
) -> CombineScoreOut:
    """Admin only.  Records a manual Combine evaluation (Pace / Shooting /
    Dribbling / Technique) for a player and appends a RatingEvent.

    Formula: overall = mean(pillars 0-100); delta = (overall - 50) * 3.0
    A perfect 100/100 combine gives +150 rating; 0/100 gives -150.
    """
    player = await db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    sp_row = await db.execute(
        select(SportProfile).where(
            SportProfile.player_id == player_id,
            SportProfile.sport == payload.sport,
        )
    )
    profile = sp_row.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {payload.sport} sport profile found for this player",
        )

    overall = (payload.pace + payload.shooting + payload.dribbling + payload.technique) / 4.0
    delta = (overall - 50.0) * 3.0
    new_rating = max(0.0, profile.current_rating + delta)

    # APPEND ONLY — never update existing rating_events rows.
    db.add(
        RatingEvent(
            player_id=player_id,
            sport=payload.sport,
            match_id=None,
            rating_before=profile.current_rating,
            rating_after=new_rating,
            delta=delta,
            algorithm_version="combine_v1",
            source_type=RatingSourceType.COACH_ASSESSMENT.value,
            source_id=player_id,  # the player is the subject of the assessment
            breakdown={
                "pace": payload.pace,
                "shooting": payload.shooting,
                "dribbling": payload.dribbling,
                "technique": payload.technique,
                "overall": round(overall, 2),
                "notes": payload.notes,
            },
        )
    )

    # Update denormalized cache — the event log is the source of truth.
    profile.current_rating = new_rating

    await db.commit()

    return CombineScoreOut(
        player_id=player_id,
        sport=payload.sport,
        pace=payload.pace,
        shooting=payload.shooting,
        dribbling=payload.dribbling,
        technique=payload.technique,
        overall=round(overall, 2),
        rating_delta=round(delta, 4),
        new_rating=round(new_rating, 4),
        notes=payload.notes,
    )
