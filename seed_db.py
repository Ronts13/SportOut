#!/usr/bin/env python3
"""
seed_db.py — Populates the SportOut database with Football-focused test data.

Run from repo root:
    python seed_db.py            # insert if DB is empty (idempotent)
    python seed_db.py --reset    # truncate ALL tables, then re-insert

Seed accounts (all share the same password):
    Password: SportOut123!

All players appear on the Football (soccer) leaderboard by default.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime, time as dtime, timedelta, timezone

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
# Primary sport is soccer for all players. Ratings map to display scale 40-95.
PLAYERS: list[tuple] = [
    # ── Elite tier (display 75+) ──────────────────────────────────────────
    ("Tal Peretz",      "tal_p",    "tal@seed.sportout.test",    "Tel Aviv",  1994,
     [("soccer", 1450.0, 40, 45)]),
    ("Omer Ben-Ami",    "omer_ba",  "omer@seed.sportout.test",   "Tel Aviv",  1997,
     [("soccer", 1380.0, 35, 43)]),
    ("Itai Friedman",   "itai_f",  "itai@seed.sportout.test",   "Herzliya",  1992,
     [("soccer", 1340.0, 30, 40)]),
    ("Yonatan Levy",    "yoni_l",   "yoni@seed.sportout.test",   "Tel Aviv",  1999,
     [("soccer", 1310.0, 28, 38)]),

    # ── Gold tier (display 65-74) ─────────────────────────────────────────
    ("Ron Tsemakhman",  "ron_ts",   "ron.ts@seed.sportout.test", "Tel Aviv",  2001,
     [("soccer", 1260.0, 24, 34)]),
    ("Lior Khaytov",    "lior_kh",  "lior@seed.sportout.test",   "Tel Aviv",  2000,
     [("soccer", 1220.0, 20, 32)]),
    ("Guy Shachar",     "guy_sh",   "guy@seed.sportout.test",    "Tel Aviv",  1998,
     [("soccer", 1190.0, 18, 30)]),
    ("Aviram Shuster",  "aviram_s", "aviram@seed.sportout.test", "Ramat Gan", 1993,
     [("soccer", 1160.0, 16, 28)]),

    # ── Silver tier (display 55-64) ───────────────────────────────────────
    ("Shira Dagan",     "shira_d",  "shira@seed.sportout.test",  "Tel Aviv",  2000,
     [("soccer", 1120.0, 14, 26)]),
    ("Mor Katz",        "mor_k",    "mor@seed.sportout.test",    "Tel Aviv",  2003,
     [("soccer", 1090.0, 11, 24)]),
    ("Dan Haim Lee",    "dan_hl",   "dan@seed.sportout.test",    "Tel Aviv",  1996,
     [("soccer", 1060.0, 9, 22)]),
    ("Amit Grossman",   "amit_g",   "amit@seed.sportout.test",   "Rishon",    1991,
     [("soccer", 1030.0, 7, 20)]),

    # ── Bronze tier (display 40-54) ───────────────────────────────────────
    ("Noa Cohen",       "noa_c",    "noa@seed.sportout.test",    "Tel Aviv",  2002,
     [("soccer", 980.0,  5, 18)]),
    ("Liran Malki",     "liran_m",  "liran@seed.sportout.test",  "Tel Aviv",  1997,
     [("soccer", 950.0,  3, 16)]),
    ("Mia Rosen",       "mia_r",    "mia@seed.sportout.test",    "Tel Aviv",  2001,
     [("soccer", 920.0,  2, 14)]),
    ("Ron Ben-David",   "ron_bd",   "ron@seed.sportout.test",    "Tel Aviv",  1998,
     [("soccer", 900.0,  1, 12)]),

    # ── Non-soccer players (variety) ─────────────────────────────────────
    ("Kobi Bar",        "kobi_bar", "kobi@seed.sportout.test",   "Tel Aviv",  1995,
     [("padel", 1350.0, 31, 38), ("soccer", 1050.0, 8, 18)]),
    ("Ofir Tuti",       "ofir_t",   "ofir@seed.sportout.test",   "Tel Aviv",  1999,
     [("basketball", 1340.0, 25, 34), ("soccer", 970.0, 4, 16)]),
]

# (name, street, city, lat, lon, sports, opens, closes, operating_days, amenities, courts)
FACILITIES: list[dict] = [
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
            ("5-a-side Pitch",     "soccer",     "asphalt",  False, 10, True),
            ("7-a-side Pitch",     "soccer",     "synthetic_grass", False, 14, True),
        ],
    },
    {
        "name": "Sportek Tel Aviv",
        "street": "Rokach Blvd 1",
        "city": "Tel Aviv",
        "lat": 32.0856, "lon": 34.7916,
        "sports": ["padel", "tennis", "soccer"],
        "opens": (7, 0), "closes": (23, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"parking": True, "showers": True, "cafe": True},
        "courts": [
            ("Padel Court 1",    "padel",  "synthetic_grass", False, 4,  True),
            ("Padel Court 2",    "padel",  "synthetic_grass", False, 4,  True),
            ("Football Cage",   "soccer", "synthetic_grass", True,  10, True),
        ],
    },
    {
        "name": "Wolfson Stadium Pitches",
        "street": "Wolfson St 1, Holon",
        "city": "Holon",
        "lat": 32.0099, "lon": 34.7875,
        "sports": ["soccer"],
        "opens": (8, 0), "closes": (22, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"parking": True, "showers": True},
        "courts": [
            ("Main Pitch",   "soccer", "natural_grass",    False, 22, True),
            ("Side Pitch 1", "soccer", "synthetic_grass",  False, 14, True),
        ],
    },
    {
        "name": "Ramat Gan National Park Courts",
        "street": "Abba Hillel 25",
        "city": "Ramat Gan",
        "lat": 32.0833, "lon": 34.8167,
        "sports": ["soccer", "basketball"],
        "opens": (6, 0), "closes": (21, 0),
        "days": [0, 1, 2, 3, 4, 5, 6],
        "amenities": {"water_fountain": True},
        "courts": [
            ("Football Court A", "soccer",     "asphalt", False, 10, True),
            ("Basketball Court", "basketball", "asphalt", False, 10, True),
        ],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _point(lon: float, lat: float) -> WKTElement:
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
            select(User).where(User.email == "tal@seed.sportout.test").limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            if not reset:
                print("Database already contains seed data.")
                print("Run with --reset to truncate all tables and re-seed.")
                return
            print("Truncating all tables...")
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
            await db.flush()

            player = Player(
                id=user.id,
                display_name=name,
                username=username,
                city=city,
                date_of_birth=date(dob_year, 6, 15),
                card_is_public=True,
            )
            db.add(player)
            await db.flush()

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

        players_list = list(player_rows.values())
        bloom     = facility_rows["Bloomfield Stadium Area"]
        hayarkon  = facility_rows["Park Hayarkon Sports Complex"]
        sportek   = facility_rows["Sportek Tel Aviv"]
        wolfson   = facility_rows["Wolfson Stadium Pitches"]
        ramatgan  = facility_rows["Ramat Gan National Park Courts"]

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

        # M1 — Open 5v5 at Bloomfield (tomorrow evening)  ← hero match
        m1 = _match(
            sport="soccer",
            facility_id=bloom.id,
            created_by_id=players_list[0].id,   # Tal Peretz
            scheduled_at=_in_days(1, 19),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=10,
            min_rating=1000.0,
            max_rating=1500.0,
        )
        await db.flush()
        _roster(m1, players_list[0])   # Tal Peretz
        _roster(m1, players_list[1])   # Omer Ben-Ami
        _roster(m1, players_list[3])   # Yonatan Levy

        # M2 — Open 5-a-side at Hayarkon (tomorrow)
        m2 = _match(
            sport="soccer",
            facility_id=hayarkon.id,
            created_by_id=players_list[2].id,   # Itai Friedman
            scheduled_at=_in_days(1, 18),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=10,
        )
        await db.flush()
        _roster(m2, players_list[2])   # Itai Friedman
        _roster(m2, players_list[4])   # Ron Tsemakhman
        _roster(m2, players_list[7])   # Aviram Shuster

        # M3 — Elite bracket at Bloomfield (3 days out)
        m3 = _match(
            sport="soccer",
            facility_id=bloom.id,
            created_by_id=players_list[1].id,   # Omer Ben-Ami
            scheduled_at=_in_days(3, 20),
            format=MatchFormat.SCRIMMAGE.value,
            status="open",
            max_players=10,
            min_rating=1200.0,
            max_rating=1600.0,
        )
        await db.flush()
        _roster(m3, players_list[1])   # Omer Ben-Ami
        _roster(m3, players_list[2])   # Itai Friedman

        # M4 — Casual 5v5 at Hayarkon (4 days out) — no bracket
        m4 = _match(
            sport="soccer",
            facility_id=hayarkon.id,
            created_by_id=players_list[8].id,   # Shira Dagan
            scheduled_at=_in_days(4, 17),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=10,
        )
        await db.flush()
        _roster(m4, players_list[8])   # Shira Dagan
        _roster(m4, players_list[9])   # Mor Katz

        # M5 — Gold bracket at Wolfson (5 days out)
        m5 = _match(
            sport="soccer",
            facility_id=wolfson.id,
            created_by_id=players_list[5].id,   # Lior Khaytov
            scheduled_at=_in_days(5, 19),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=14,
            min_rating=1100.0,
            max_rating=1400.0,
        )
        await db.flush()
        _roster(m5, players_list[5])   # Lior Khaytov
        _roster(m5, players_list[6])   # Guy Shachar

        # M6 — Cage match at Sportek (tomorrow, small format)
        m6 = _match(
            sport="soccer",
            facility_id=sportek.id,
            created_by_id=players_list[3].id,   # Yonatan Levy
            scheduled_at=_in_days(1, 20),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=6,
        )
        await db.flush()
        _roster(m6, players_list[3])   # Yonatan Levy

        # M7 — Completed match at Bloomfield (yesterday) — 3-1 home win
        m7 = _match(
            sport="soccer",
            facility_id=bloom.id,
            created_by_id=players_list[0].id,
            scheduled_at=_in_days(-1, 18),
            format=MatchFormat.SCRIMMAGE.value,
            status="completed",
            max_players=10,
            home_score=3,
            away_score=1,
            result_confirmed_at=_in_days(-1, 21),
        )
        await db.flush()
        _roster(m7, players_list[0],  "home")  # Tal Peretz
        _roster(m7, players_list[4],  "home")  # Ron Tsemakhman
        _roster(m7, players_list[3],  "away")  # Yonatan Levy
        _roster(m7, players_list[1],  "away")  # Omer Ben-Ami

        # M8 — Basketball at Hayarkon (tomorrow, variety)
        m8 = _match(
            sport="basketball",
            facility_id=hayarkon.id,
            created_by_id=players_list[17].id,  # Ofir Tuti
            scheduled_at=_in_days(2, 17),
            format=MatchFormat.PICKUP.value,
            status="open",
            max_players=10,
        )
        await db.flush()
        _roster(m8, players_list[17])  # Ofir Tuti

        await db.commit()
        print("  8 matches created (7 soccer open/completed + 1 basketball)")

        print("\nDone! Seed summary:")
        print(f"  Players   : {len(PLAYERS)}")
        print(f"  Profiles  : {sport_profile_count}")
        print(f"  Facilities: {len(FACILITIES)}")
        print(f"  Matches   : 8 (7 soccer, 1 basketball)")
        print(f"\n  Login with any @seed.sportout.test email")
        print(f"  Password : SportOut123!")
        print(f"\n  Top player: tal@seed.sportout.test (rating 1450, display ~82)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the SportOut database.")
    parser.add_argument("--reset", action="store_true",
                        help="TRUNCATE all tables before seeding (destructive — dev only).")
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
