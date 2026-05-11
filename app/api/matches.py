from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import TokenData, get_current_user
from app.core.database import get_db
from app.models.facility import Facility
from app.models.match import Match, MatchResultConfirmation, MatchRoster
from app.models.sport_profile import SportProfile
from app.schemas.match import MatchCreate, MatchOut, MatchResultSubmit, PlayerGameStatsCreate

router = APIRouter(prefix="/matches", tags=["matches"])

_WITH_ROSTERS = selectinload(Match.rosters)


async def _get_match_or_404(match_id: uuid.UUID, db: AsyncSession) -> Match:
    match = await db.get(Match, match_id, options=[_WITH_ROSTERS])
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


async def _require_rostered(match: Match, player_id: uuid.UUID) -> None:
    if not any(r.player_id == player_id for r in match.rosters):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not rostered in this match",
        )


@router.post("/", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
async def create_match(
    payload: MatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> MatchOut:
    player_id = uuid.UUID(current_user.user_id)
    match = Match(
        sport=payload.sport,
        facility_id=payload.facility_id,
        court_id=payload.court_id,
        created_by_id=player_id,
        scheduled_at=payload.scheduled_at,
        format=payload.format,
        is_private=payload.is_private,
        min_rating=payload.min_rating,
        max_rating=payload.max_rating,
        max_players=payload.max_players,
        status="open",
    )
    db.add(match)
    await db.flush()  # populate match.id before creating the creator's roster entry

    db.add(MatchRoster(match_id=match.id, player_id=player_id, team="none", confirmed=True))
    await db.commit()

    result = await db.execute(select(Match).where(Match.id == match.id).options(_WITH_ROSTERS))
    return MatchOut.model_validate(result.scalar_one())


@router.get("/", response_model=list[MatchOut])
async def list_matches(
    sport: str | None = Query(None),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    radius_km: float = Query(10.0, ge=0.1, le=100.0),
    min_rating: float | None = Query(None, ge=0),
    max_rating: float | None = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> list[MatchOut]:
    stmt = (
        select(Match)
        .where(Match.status == "open", Match.is_private.is_(False))
        .options(_WITH_ROSTERS)
        .order_by(Match.scheduled_at)
        .limit(limit)
    )

    if sport is not None:
        stmt = stmt.where(Match.sport == sport)

    if lat is not None and lon is not None:
        caller_point = cast(
            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
            Geography,
        )
        stmt = stmt.join(Facility, Match.facility_id == Facility.id).where(
            func.ST_DWithin(cast(Facility.location, Geography), caller_point, radius_km * 1000)
        )

    # Filter to matches whose rating bracket overlaps the provided range.
    # min_rating param = caller's minimum acceptable rating floor →
    #   exclude matches whose cap is below this value.
    if min_rating is not None:
        stmt = stmt.where((Match.max_rating.is_(None)) | (Match.max_rating >= min_rating))

    # max_rating param = caller's maximum acceptable rating ceiling →
    #   exclude matches whose floor is above this value.
    if max_rating is not None:
        stmt = stmt.where((Match.min_rating.is_(None)) | (Match.min_rating <= max_rating))

    rows = await db.execute(stmt)
    return [MatchOut.model_validate(m) for m in rows.scalars()]


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> MatchOut:
    return MatchOut.model_validate(await _get_match_or_404(match_id, db))


@router.post("/{match_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    player_id = uuid.UUID(current_user.user_id)
    match = await _get_match_or_404(match_id, db)

    if match.status != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is not open for joining")

    if len(match.rosters) >= match.max_players:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is full")

    if any(r.player_id == player_id for r in match.rosters):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already joined this match")

    # Enforce rating bracket when the match has one set.
    if match.min_rating is not None or match.max_rating is not None:
        profile_row = await db.execute(
            select(SportProfile).where(
                SportProfile.player_id == player_id,
                SportProfile.sport == match.sport,
            )
        )
        profile = profile_row.scalar_one_or_none()
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No {match.sport} sport profile found; cannot verify rating bracket",
            )
        r = profile.current_rating
        if match.min_rating is not None and r < match.min_rating:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rating {r:.0f} is below match minimum {match.min_rating:.0f}",
            )
        if match.max_rating is not None and r > match.max_rating:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rating {r:.0f} is above match maximum {match.max_rating:.0f}",
            )

    db.add(MatchRoster(match_id=match_id, player_id=player_id, team="none", confirmed=False))
    await db.commit()


@router.delete("/{match_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    player_id = uuid.UUID(current_user.user_id)
    match = await _get_match_or_404(match_id, db)

    if match.status in ("in_progress", "completed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot leave a match that is in progress or completed",
        )

    roster_row = await db.execute(
        select(MatchRoster).where(
            MatchRoster.match_id == match_id,
            MatchRoster.player_id == player_id,
        )
    )
    roster = roster_row.scalar_one_or_none()
    if roster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not in this match")

    await db.delete(roster)
    await db.commit()


@router.post("/{match_id}/result", response_model=MatchOut)
async def submit_result(
    match_id: uuid.UUID,
    payload: MatchResultSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> MatchOut:
    player_id = uuid.UUID(current_user.user_id)
    match = await _get_match_or_404(match_id, db)

    await _require_rostered(match, player_id)

    if match.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is cancelled")

    if match.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Result already submitted; use the confirm endpoint to validate it",
        )

    match.home_score = payload.home_score
    match.away_score = payload.away_score
    match.mvp_player_id = payload.mvp_player_id
    match.status = "completed"
    await db.commit()

    result = await db.execute(select(Match).where(Match.id == match_id).options(_WITH_ROSTERS))
    return MatchOut.model_validate(result.scalar_one())


@router.post("/{match_id}/result/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_result(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Each rostered player casts one confirmation vote.  Once >= 50% of rostered
    players have confirmed, result_confirmed_at is stamped and the rating
    recalculation task is enqueued.
    """
    player_id = uuid.UUID(current_user.user_id)
    match = await _get_match_or_404(match_id, db)

    if match.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A result must be submitted before it can be confirmed",
        )

    await _require_rostered(match, player_id)

    # Idempotent: if quorum already reached there is nothing left to do.
    if match.result_confirmed_at is not None:
        return

    # Guard against double-confirmation from the same player.
    existing = await db.execute(
        select(MatchResultConfirmation).where(
            MatchResultConfirmation.match_id == match_id,
            MatchResultConfirmation.player_id == player_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already confirmed this result",
        )

    db.add(MatchResultConfirmation(match_id=match_id, player_id=player_id))
    await db.flush()

    # Count total confirmations after the flush so we include the new row.
    conf_count_row = await db.execute(
        select(func.count()).select_from(MatchResultConfirmation).where(
            MatchResultConfirmation.match_id == match_id
        )
    )
    conf_count: int = conf_count_row.scalar_one()
    roster_count = len(match.rosters)

    # Quorum: >= 50% of rostered players have confirmed.
    if conf_count * 2 >= roster_count:
        match.result_confirmed_at = datetime.now(timezone.utc)
        await db.flush()
        # Late import keeps module-level import graph clean and avoids circular deps.
        from app.workers.ratings import recalculate_match_ratings  # noqa: PLC0415
        recalculate_match_ratings.delay(str(match_id))

    await db.commit()


@router.post("/{match_id}/stats", status_code=status.HTTP_201_CREATED)
async def submit_game_stats(
    match_id: uuid.UUID,
    payload: PlayerGameStatsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    raise NotImplementedError
