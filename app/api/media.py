from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.media import HighlightOut, ManualUploadRequest, MediaSessionOut

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload", response_model=MediaSessionOut, status_code=status.HTTP_201_CREATED)
async def submit_manual_upload(
    payload: ManualUploadRequest,
    db: AsyncSession = Depends(get_db),
) -> MediaSessionOut:
    """Creates a MediaSession from a manually uploaded S3 video and enqueues highlight generation."""
    raise NotImplementedError


@router.get("/sessions/{session_id}", response_model=MediaSessionOut)
async def get_media_session(
    session_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> MediaSessionOut:
    raise NotImplementedError


@router.get("/highlights/{highlight_id}", response_model=HighlightOut)
async def get_highlight(
    highlight_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> HighlightOut:
    raise NotImplementedError


@router.patch("/highlights/{highlight_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_highlight_visibility(
    highlight_id: uuid.UUID,
    is_public: bool,
    db: AsyncSession = Depends(get_db),
):
    raise NotImplementedError
