from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.adapters.filming import HighlightRequest, get_provider
from app.api.dependencies import TokenData, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.match import Match, MatchRoster
from app.models.media import Highlight, MediaSession
from app.schemas.media import HighlightOut, ManualUploadRequest, MediaSessionOut

router = APIRouter(prefix="/media", tags=["media"])

_WITH_HIGHLIGHTS = selectinload(MediaSession.highlights)


@router.post("/upload", response_model=MediaSessionOut, status_code=status.HTTP_201_CREATED)
async def submit_manual_upload(
    payload: ManualUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> MediaSessionOut:
    """Creates a MediaSession from a player-uploaded S3 video and immediately
    generates highlight records via the ManualUploadAdapter (no CV processing).
    One session per match — duplicate uploads are rejected with 409.
    """
    match = await db.get(Match, payload.match_id, options=[selectinload(Match.rosters)])
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    existing = await db.execute(
        select(MediaSession).where(MediaSession.match_id == payload.match_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A media session already exists for this match",
        )

    # Construct the canonical S3 URL from the uploaded object key.
    base_url = settings.S3_ENDPOINT_URL or f"https://s3.{settings.S3_REGION}.amazonaws.com"
    raw_footage_url = f"{base_url}/{settings.S3_BUCKET}/{payload.file_key}"

    session = MediaSession(
        match_id=payload.match_id,
        provider="manual_upload",
        raw_footage_url=raw_footage_url,
        processing_status="complete",  # no async CV pipeline for manual uploads
        completed_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()  # populate session.id before creating child highlights

    provider = get_provider("manual_upload")
    for roster_entry in match.rosters:
        req = HighlightRequest(
            media_session_id=session.id,
            player_id=roster_entry.player_id,
            raw_footage_url=raw_footage_url,
            duration_seconds=payload.duration_seconds,
        )
        results = await provider.generate_highlights(req)
        for res in results:
            db.add(
                Highlight(
                    media_session_id=session.id,
                    player_id=res.player_id,
                    match_id=payload.match_id,
                    duration_seconds=res.duration_seconds,
                    event_tags=res.event_tags,
                    url=res.url,
                    thumbnail_url=res.thumbnail_url,
                    is_public=True,
                )
            )

    await db.commit()

    refreshed = await db.execute(
        select(MediaSession).where(MediaSession.id == session.id).options(_WITH_HIGHLIGHTS)
    )
    return MediaSessionOut.model_validate(refreshed.scalar_one())


@router.get("/sessions/{session_id}", response_model=MediaSessionOut)
async def get_media_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> MediaSessionOut:
    result = await db.execute(
        select(MediaSession).where(MediaSession.id == session_id).options(_WITH_HIGHLIGHTS)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media session not found")
    return MediaSessionOut.model_validate(session)


@router.get("/highlights/{highlight_id}", response_model=HighlightOut)
async def get_highlight(
    highlight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
) -> HighlightOut:
    highlight = await db.get(Highlight, highlight_id)
    if highlight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight not found")
    return HighlightOut.model_validate(highlight)


@router.patch("/highlights/{highlight_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_highlight_visibility(
    highlight_id: uuid.UUID,
    is_public: bool,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    highlight = await db.get(Highlight, highlight_id)
    if highlight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight not found")

    if str(highlight.player_id) != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your highlight")

    highlight.is_public = is_public
    await db.commit()
