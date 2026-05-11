from __future__ import annotations

import uuid
from datetime import datetime, time

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.facility import CourtLiveUpdate, CourtOut, FacilityCreate, FacilityOut

router = APIRouter(prefix="/facilities", tags=["facilities"])

# ---------------------------------------------------------------------------
# Mock data — 3 Israeli courts matching the frontend map markers
# ---------------------------------------------------------------------------
_TS = datetime(2024, 1, 1, 12, 0, 0)

_MOCK_FACILITIES: list[FacilityOut] = [
    FacilityOut(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Sportek Tel Aviv",
        address_street="Rokach Blvd 1",
        address_city="Tel Aviv",
        latitude=32.0856,
        longitude=34.7916,
        sports_supported=["padel"],
        opens_at=time(7, 0),
        closes_at=time(23, 0),
        operating_days=[0, 1, 2, 3, 4, 5, 6],
        amenities={"parking": True, "showers": True, "cafe": True},
        is_active=True,
        courts=[
            CourtOut(
                id=uuid.UUID("00000000-0000-0000-0001-000000000001"),
                facility_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="Padel Court 1",
                sport="padel",
                surface="artificial_grass",
                indoor=False,
                lighting_available=True,
                lighting_on=True,
                current_occupancy=2,
                max_capacity=4,
                condition="good",
                condition_note=None,
                is_bookable=True,
                updated_at=_TS,
            ),
            CourtOut(
                id=uuid.UUID("00000000-0000-0000-0001-000000000002"),
                facility_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="Padel Court 2",
                sport="padel",
                surface="artificial_grass",
                indoor=False,
                lighting_available=True,
                lighting_on=True,
                current_occupancy=0,
                max_capacity=4,
                condition="good",
                condition_note=None,
                is_bookable=True,
                updated_at=_TS,
            ),
        ],
    ),
    FacilityOut(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        name="Dubnov Park Courts",
        address_street="Dubnov St 12",
        address_city="Tel Aviv",
        latitude=32.0801,
        longitude=34.7793,
        sports_supported=["tennis"],
        opens_at=time(6, 0),
        closes_at=time(22, 0),
        operating_days=[0, 1, 2, 3, 4, 5, 6],
        amenities={"parking": False, "showers": False},
        is_active=True,
        courts=[
            CourtOut(
                id=uuid.UUID("00000000-0000-0000-0002-000000000001"),
                facility_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                name="Tennis Court 1",
                sport="tennis",
                surface="clay",
                indoor=False,
                lighting_available=True,
                lighting_on=False,
                current_occupancy=0,
                max_capacity=4,
                condition="good",
                condition_note=None,
                is_bookable=True,
                updated_at=_TS,
            ),
        ],
    ),
    FacilityOut(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        name="Padel Expo Tel Aviv",
        address_street="HaMasger St 60",
        address_city="Tel Aviv",
        latitude=32.1070,
        longitude=34.8430,
        sports_supported=["padel"],
        opens_at=time(8, 0),
        closes_at=time(22, 0),
        operating_days=[0, 1, 2, 3, 4],
        amenities={"parking": True, "showers": True},
        is_active=False,
        courts=[],
    ),
]


@router.get("/", response_model=list[FacilityOut])
async def list_facilities(
    sport: str | None = Query(None),
) -> list[FacilityOut]:
    if sport is None:
        return _MOCK_FACILITIES
    return [f for f in _MOCK_FACILITIES if sport in f.sports_supported]


@router.post("/", response_model=FacilityOut, status_code=status.HTTP_201_CREATED)
async def create_facility(payload: FacilityCreate, db: AsyncSession = Depends(get_db)) -> FacilityOut:
    raise NotImplementedError


@router.get("/nearby", response_model=list[FacilityOut])
async def get_nearby_facilities(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, ge=0.1, le=50.0),
    sport: str | None = Query(None),
) -> list[FacilityOut]:
    """Mock: returns 3 hardcoded Israeli courts. Real impl will use PostGIS ST_DWithin."""
    if sport is None:
        return _MOCK_FACILITIES
    return [f for f in _MOCK_FACILITIES if sport in f.sports_supported]


@router.get("/{facility_id}", response_model=FacilityOut)
async def get_facility(facility_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> FacilityOut:
    raise NotImplementedError


@router.patch("/courts/{court_id}/live", response_model=CourtOut)
async def update_court_live_status(
    court_id: uuid.UUID,
    payload: CourtLiveUpdate,
    db: AsyncSession = Depends(get_db),
) -> CourtOut:
    """Manager endpoint to push real-time court state: lights, occupancy, condition."""
    raise NotImplementedError
