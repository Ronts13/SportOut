from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.facility import Facility
from app.schemas.facility import CourtLiveUpdate, CourtOut, FacilityCreate, FacilityOut

router = APIRouter(prefix="/facilities", tags=["facilities"])


def _facility_to_out(f: Facility) -> FacilityOut:
    point = to_shape(f.location)
    return FacilityOut(
        id=f.id,
        name=f.name,
        address_street=f.address_street,
        address_city=f.address_city,
        latitude=point.y,
        longitude=point.x,
        sports_supported=f.sports_supported,
        opens_at=f.opens_at,
        closes_at=f.closes_at,
        operating_days=f.operating_days,
        amenities=f.amenities,
        is_active=f.is_active,
        courts=[CourtOut.model_validate(c) for c in f.courts],
    )


@router.get("/", response_model=list[FacilityOut])
async def list_facilities(
    sport: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityOut]:
    stmt = (
        select(Facility)
        .where(Facility.is_active.is_(True))
        .options(selectinload(Facility.courts))
        .order_by(Facility.name)
    )
    if sport is not None:
        stmt = stmt.where(Facility.sports_supported.any(sport))
    rows = await db.execute(stmt)
    return [_facility_to_out(f) for f in rows.scalars().all()]


@router.post("/", response_model=FacilityOut, status_code=status.HTTP_201_CREATED)
async def create_facility(payload: FacilityCreate, db: AsyncSession = Depends(get_db)) -> FacilityOut:
    raise NotImplementedError


@router.get("/nearby", response_model=list[FacilityOut])
async def get_nearby_facilities(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, ge=0.1, le=50.0),
    sport: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[FacilityOut]:
    caller = cast(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326), Geography)
    stmt = (
        select(Facility)
        .where(
            Facility.is_active.is_(True),
            func.ST_DWithin(cast(Facility.location, Geography), caller, radius_km * 1000),
        )
        .options(selectinload(Facility.courts))
    )
    if sport is not None:
        stmt = stmt.where(Facility.sports_supported.any(sport))
    rows = await db.execute(stmt)
    return [_facility_to_out(f) for f in rows.scalars().all()]


@router.get("/{facility_id}", response_model=FacilityOut)
async def get_facility(facility_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> FacilityOut:
    raise NotImplementedError


@router.patch("/courts/{court_id}/live", response_model=CourtOut)
async def update_court_live_status(
    court_id: uuid.UUID,
    payload: CourtLiveUpdate,
    db: AsyncSession = Depends(get_db),
) -> CourtOut:
    raise NotImplementedError
