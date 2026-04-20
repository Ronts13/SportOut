from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HighlightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    media_session_id: uuid.UUID
    player_id: uuid.UUID
    match_id: uuid.UUID
    duration_seconds: int
    event_tags: list[str]
    url: str
    thumbnail_url: str | None
    is_public: bool
    view_count: int
    generated_at: datetime


class MediaSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    provider: str
    processing_status: str
    video_metrics: dict | None
    created_at: datetime
    completed_at: datetime | None
    highlights: list[HighlightOut] = []


class ManualUploadRequest(BaseModel):
    match_id: uuid.UUID
    file_key: str = Field(..., description="S3 object key of the pre-uploaded video file")
    duration_seconds: int = Field(..., ge=1)
