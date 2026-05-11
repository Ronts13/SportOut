#!/usr/bin/env python3
"""
seed_db.py — Populates the SportOut database with realistic test data.

Run from repo root:
    python seed_db.py            # insert if DB is empty (idempotent)
    python seed_db.py --reset    # truncate ALL tables, then re-insert

Seed accounts (all share the same password):
    Password: SportOut123!
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime, time as dtime, timedelta, timezone

# ── Allow imports from the project root ──────────────────────────────────────
sys.path.insert(0, ".")

from geoalchemy2.elements import WKTElement
from sqlalchemy import select, text

import bcrypt as _bcrypt

from app.core.database import AsyncSessionFactory
from app.core.enums import MatchFormat, UserRole
from app.models.facility import Court, Facility
from app.models.match import Match, MatchRoster
from app.models.player import Player
from app.models.sport_profile import SportProfile
from app.models.user import User


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_PW = _bcrypt.hashpw(b"SportOut123!", _bcrypt.gensalt()).decode()

# (display_name, username, email, city, dob_year, [(sport, rating, wins, games)])
PLAYERS: list[tuple] = [
    ("Ron Ben-David",   "ron_bd",    "ron@seed.sportout.test",    "Tel Aviv",  1998, [("padel", 1420.0, 38, 42), ("tennis", 1380.0, 30, 38)]),
    ("Kobi Bar",        "kobi_bar",  "kobi@seed.sportout.test",   "Tel Aviv",  1995, [("padel", 1350.0, 31, 38)]),
    ("Lior Khaytov",    "lior_kh",   "lior.kh@seed.sportout.test","Tel Aviv",  2000, [("padel", 1280.0, 28, 36), ("soccer", 1190.0, 22, 30)]),
    ("Liran Malki",     "liran_m",   "liran@seed.sportout.test",  "Tel Aviv",  1997, [("padel", 1210.0, 22, 32), ("basketball", 1150.0, 18, 28)]),
    ("Ofir Tuti",       "ofir_t",    "ofir@seed.sportout.test",   "Tel Aviv",  1999, [("tennis", 1340.0, 25, 34), ("padel", 1170.0, 18, 28)]),
    ("Dan Haim Lee",    "dan_hl",    "dan@seed.sportout.test",    "Tel Aviv",  1996, [("tennis", 1260.0, 15, 24)]),
    ("Ron Tsemakhman",  "ron_ts",    "ron.ts@seed.sportout.test", "Tel Aviv",  2001, [("padel", 1150.0, 12, 22), ("soccer", 1240.0, 20, 26)]),
    ("Aviram Shuster",  "aviram_s",  "aviram@seed.sportout.test", "Ramat Gan", 1993, [("tennis", 1180.0, 9,  20), ("basketball", 1310.0, 29, 36)]),
    ("Tal Peretz",      "tal_p",     "tal@seed.sportout.test",    "Tel Aviv",  1994, [("soccer", 1450.0, 40, 45), ("padel", 980.0, 8, 18)]),
    ("Noa Cohen",       "noa_c",     "noa@seed.sportout.test",    "Tel Aviv",  2002, [("padel", 1360.0, 33, 40)]),
    ("Itai Friedman",   "itai_f",    "itai@seed.sportout.test",   "Herzliya",  1992, [("basketball", 1420.0, 36, 42), ("soccer", 1100.0, 14, 24)]),
    ("Mor Katz",        "mor_k",     "mor@seed.sportout.test",    "Tel Aviv",  2003, [("tennis", 1120.0, 10, 22)]),
    ("Yonatan Levy",    "yoni_l",    "yoni@seed.sportout.test",   "Tel Aviv",  1999, [("soccer", 1280.0, 25, 34)]),
    ("Shira Dagan",     "shira_d",   "shira@seed.sportout.test",  "Tel Aviv",  2000, [("padel", 1310.0, 30, 38), ("tennis", 1200.0, 16, 26)]),
    ("Amit Grossman",   "amit_g",    "amit@seed.sportout.test",   "Rishon",    1991, [("basketball", 1380.0, 34, 40)]),
    ("Guy Shachar",     "guy_sh",    "guy@seed.sportout.test",    "Tel Aviv",  1998, [("soccer", 1180.0, 18, 30), ("padel", 1050.0, 10, 20)]),
    ("Mia Rosen",       "mia_r",     "mia@seed.sportout.test",    "Tel Aviv",  2001, [("tennis", 1410.0, 38, 44)]),
    ("Omer Ben-Ami",    "omer_ba",   "omer@seed.sportout.test",   "Tel Aviv",  1997, [("basketball", 1240.0, 22, 34), ("soccer", 1320.0, 28, 38)]),
]

# (name, street, city, lat, lon, sports_supported, opens, closes, operating_days, amenities, courts)
# courts: (name, sport, surface, indoor, max_capacity, lighting)
FACILITIES: list[dict] = [
    {
        "name": "Sportek Tel Aviv",
        "street": "Rokach Blvd 1",
        "city": "Tel Aviv",
        "lat": 32.0856, "lon": 34.7916,
        "sports": ["padel", "tennis"],
        "opens": (7, 0), "closes": (23, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"parking": True, "showers": True, "cafe": True},
        "courts": [
            ("Padel Court 1", "padel",  "synthetic_grass", False, 4,  True),
            ("Padel Court 2", "padel",  "synthetic_grass", False, 4,  True),
            ("Tennis Court A","tennis", "hardwood",        False, 4,  True),
        ],
    },
    {
        "name": "Dubnov Park Courts",
        "street": "Dubnov St 12",
        "city": "Tel Aviv",
        "lat": 32.0801, "lon": 34.7793,
        "sports": ["tennis"],
        "opens": (6, 0), "closes": (22, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"parking": False, "showers": False},
        "courts": [
            ("Tennis Court 1", "tennis", "concrete", False, 4, True),
            ("Tennis Court 2", "tennis", "concrete", False, 4, False),
        ],
    },
    {
        "name": "Padel Expo Tel Aviv",
        "street": "HaMasger St 60",
        "city": "Tel Aviv",
        "lat": 32.0740, "lon": 34.7960,
        "sports": ["padel"],
        "opens": (8, 0), "closes": (22, 0),
        "days": [0, 1, 2, 3, 4],
        "amenities": {"parking": True, "showers": True, "pro_shop": True},
        "courts": [
            ("Arena Court 1", "padel", "synthetic_grass", True, 4, True),
            ("Arena Court 2", "padel", "synthetic_grass", True, 4, True),
            ("Arena Court 3", "padel", "synthetic_grass", True, 4, True),
        ],
    },
    {
        "name": "Bloomfield Stadium Area",
        "street": "Efal St 2, Jaffa",
        "city": "Tel Aviv",
        "lat": 32.0562, "lon": 34.7677,
        "sports": ["soccer"],
        "opens": (6, 0), "closes": (22, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"parking": True, "showers": True, "lockers": True},
        "courts": [
            ("Football Pitch 1", "soccer", "synthetic_grass", False, 22, True),
            ("Football Pitch 2", "soccer", "synthetic_grass", False, 22, True),
        ],
    },
    {
        "name": "Park Hayarkon Sports Complex",
        "street": "Rokach Blvd 47",
        "city": "Tel Aviv",
        "lat": 32.1020, "lon": 34.8070,
        "sports": ["basketball", "soccer"],
        "opens": (7, 0), "closes": (21, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"parking": True, "water_fountain": True},
        "courts": [
            ("Basketball Court 1", "basketball", "asphalt",  False, 10, True),
            ("Basketball Court 2", "basketball", "concrete", False, 10, False),
            ("5-a-side Pitch",     "soccer",     "asphalt",  False, 10, True),
        ],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _point(lon: float, lat: float) -> WKTElement:
    """WKT geometry point in WGS84 (lon first — PostGIS convention)."""
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _in_days(n: int, hour: int = 18) -> datetime:
    base = _now().replace(hour=hour, minute=0, second=0, microsecond=0)
    return base + timedelta(days=n)


# ---------------------------------------------------------------------------
# Core seeder
# ---------------------------------------------------------------------------

async def _seed(reset: bool) -> None:
    async with AsyncSessionFactory() as db:

        # ── Idempotency check / reset ─────────────────────────────────────
        existing = await db.execute(
            select(User).where(User.email == "ron@seed.sportout.test").limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            if not reset:
                print("Database already contains seed data.")
                print("Run with --reset to truncate all tables and re-seed.")
                return
            print("Truncating all tables...")
            # TRUNCATE with CASCADE drops dependent rows across all tables.
            await db.execute(text("TRUNCATE TABLE users, facilities, matches CASCADE"))
            await db.commit()
            print("Done.\n")

        # ── 1. Facilities + Courts ────────────────────────────────────────
        print("Seeding facilities...")
        facility_rows: dict[str, Facility] = {}

        for fdata in FACILITIES:
            fac = Facility(
                name=fdata["name"],
                address_street=fdata["street"],
                address_city=fdata["city"],
                address_country="IL",
                location=_point(fdata["lon"], fdata["lat"]),
                sports_supported=fdata["sports"],
                opens_at=dtime(*fdata["opens"]),
                closes_at=dtime(*fdata["closes"]),
                operating_days=fdata["days"],
                amenities=fdata["amenities"],
                is_active=True,
            )
            db.add(fac)
            await db.flush()

            for cname, csport, csurf, cindoor, ccap, clighting in fdata["courts"]:
                db.add(Court(
                    facility_id=fac.id,
                    name=cname,
                    sport=csport,
                    surface=csurf,
                    indoor=cindoor,
                    max_capacity=ccap,
                    lighting_available=clighting,
                    lighting_on=clighting,
                    condition="good",
                    is_bookable=True,
                ))
            facility_rows[fdata["name"]] = fac

        await db.flush()
        print(f"  {len(facility_rows)} facilities, "
              f"{sum(len(f['courts']) for f in FACILITIES)} courts")

        # ── 2. Players + SportProfiles ────────────────────────────────────
        print("Seeding players...")
        player_rows: dict[str, Player] = {}

        for name, username, email, city, dob_year, sports in PLAYERS:
            user = User(
                email=email,
                hashed_password=_PW,
                role=UserRole.PLAYER.value,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()  # get user.id

            player = Player(
                id=user.id,  # Player shares PK with User
                display_name=name,
                username=username,
                city=city,
                date_of_birth=date(dob_year, 6, 15),
                card_is_public=True,
            )
            db.add(player)
            await db.flush()  # get player.id

            for sport, rating, wins, games in sports:
                db.add(SportProfile(
                    player_id=player.id,
                    sport=sport,
                    current_rating=rating,
                    career_wins=wins,
                    career_games=games,
                    is_public=True,
                ))
            player_rows[username] = player

        await db.flush()
        sport_profile_count = sum(len(p[5]) for p in PLAYERS)
        print(f"  {len(player_rows)} players, {sport_profile_count} sport profiles")

        # Convenience: grab player objects by index for rosters
        players_list = list(player_rows.values())
        sportek   = facility_rows["Sportek Tel Aviv"]
        dubnov    = facility_rows["Dubnov Park Courts"]
        padel_exp = facility_rows["Padel Expo Tel Aviv"]
        bloom     = facility_rows["Bloomfield Stadium Area"]
        hayarkon  = facility_rows["Park Hayarkon Sports Complex"]

        # ── 3. Matches ────────────────────────────────────────────────────
        print("Seeding matches...")

        def _match(**kwargs) -> Match:
            m = Match(**kwargs)
            db.add(m)
            return m

        def _roster(match: Match, player: Player, team: str = "none") -> None:
            db.add(MatchRoster(
                match_id=match.id,
                player_id=player.id,
                team=team,
                confirmed=True,
                attended=True,
            ))

        # M1 — Open padel at Sportek (tomorrow evening)
        m1 = _match(
            sport="padel",
            facility_id=sportek.id,
            created_by_id=players_list[0].id,
            scheduled_at=_in_days(1, 18),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=4,
            min_rating=1100.0,
            max_rating=1500.0,
        )
        await db.flush()
        _roster(m1, players_list[0])   # Ron Ben-David
        _roster(m1, players_list[1])   # Kobi Bar

        # M2 — Open tennis at Dubnov (tomorrow)
        m2 = _match(
            sport="tennis",
            facility_id=dubnov.id,
            created_by_id=players_list[4].id,
            scheduled_at=_in_days(1, 19),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=4,
        )
        await db.flush()
        _roster(m2, players_list[4])   # Ofir Tuti
        _roster(m2, players_list[5])   # Dan Haim Lee

        # M3 — Open padel at Padel Expo with bracket (3 days out)
        m3 = _match(
            sport="padel",
            facility_id=padel_exp.id,
            created_by_id=players_list[9].id,  # Noa Cohen
            scheduled_at=_in_days(3, 17),
            format=MatchFormat.SCRIMMAGE.value,
            status="open",
            max_players=4,
            min_rating=1200.0,
            max_rating=1500.0,
        )
        await db.flush()
        _roster(m3, players_list[9])

        # M4 — Open basketball at Hayarkon (tomorrow)
        m4 = _match(
            sport="basketball",
            facility_id=hayarkon.id,
            created_by_id=players_list[10].id,  # Itai Friedman
            scheduled_at=_in_days(1, 17),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=10,
        )
        await db.flush()
        _roster(m4, players_list[10])  # Itai Friedman
        _roster(m4, players_list[7])   # Aviram Shuster
        _roster(m4, players_list[14])  # Amit Grossman

        # M5 — Open soccer at Bloomfield (day after tomorrow)
        m5 = _match(
            sport="soccer",
            facility_id=bloom.id,
            created_by_id=players_list[8].id,  # Tal Peretz
            scheduled_at=_in_days(2, 20),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=10,
        )
        await db.flush()
        _roster(m5, players_list[8])   # Tal Peretz
        _roster(m5, players_list[12])  # Yonatan Levy
        _roster(m5, players_list[17])  # Omer Ben-Ami

        # M6 — Completed soccer at Bloomfield (yesterday)
        # Home: Tal Peretz + Ron Tsemakhman   Away: Yonatan Levy + Omer Ben-Ami
        m6 = _match(
            sport="soccer",
            facility_id=bloom.id,
            created_by_id=players_list[8].id,
            scheduled_at=_in_days(-1, 18),
            format=MatchFormat.SCRIMMAGE.value,
            status="completed",
            max_players=10,
            home_score=3,
            away_score=1,
            result_confirmed_at=_in_days(-1, 21),
        )
        await db.flush()
        _roster(m6, players_list[8],  "home")  # Tal Peretz
        _roster(m6, players_list[6],  "home")  # Ron Tsemakhman
        _roster(m6, players_list[12], "away")  # Yonatan Levy
        _roster(m6, players_list[17], "away")  # Omer Ben-Ami

        await db.commit()
        print("  6 matches created (5 open, 1 completed 3-1 soccer)")

        print("\nDone! Seed summary:")
        print(f"  Players  : {len(PLAYERS)}")
        print(f"  Profiles : {sport_profile_count} (across padel, tennis, soccer, basketball)")
        print(f"  Facilities: {len(FACILITIES)} Tel Aviv venues")
        print(f"  Matches  : 6 (5 open, 1 completed)")
        print(f"\n  Login with any @seed.sportout.test email, password: SportOut123!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the SportOut database with test data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="TRUNCATE all tables before seeding (destructive — dev only).",
    )
    args = parser.parse_args()

    if args.reset:
        print("WARNING: --reset will erase ALL data in the database.")
        confirm = input("Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(_seed(reset=args.reset))


if __name__ == "__main__":
    main()
