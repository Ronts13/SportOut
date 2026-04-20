from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.match import MatchCreate, MatchOut, MatchResultSubmit, PlayerGameStatsCreate

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
async def create_match(payload: MatchCreate, db: AsyncSession = Depends(get_db)) -> MatchOut:
    raise NotImplementedError


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
) -> list[MatchOut]:
    raise NotImplementedError


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(match_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> MatchOut:
    raise NotImplementedError


@router.post("/{match_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_match(match_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError


@router.delete("/{match_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_match(match_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError


@router.post("/{match_id}/result", response_model=MatchOut)
async def submit_result(
    match_id: uuid.UUID,
    payload: MatchResultSubmit,
    db: AsyncSession = Depends(get_db),
) -> MatchOut:
    raise NotImplementedError


@router.post("/{match_id}/result/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_result(match_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Player confirms the submitted result. Once quorum is reached, triggers rating recalculation."""
    raise NotImplementedError


@router.post("/{match_id}/stats", status_code=status.HTTP_201_CREATED)
async def submit_game_stats(
    match_id: uuid.UUID,
    payload: PlayerGameStatsCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raise NotImplementedError
