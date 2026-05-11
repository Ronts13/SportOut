#!/usr/bin/env python3
"""Wipe all rows from every SportOut table without dropping any table structure.

Run this from the project root:
    python wipe_db.py

The script reads DATABASE_URL from the .env file (falls back to the default
local dev URL). It uses TRUNCATE ... CASCADE so FK order does not matter.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys


def _load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ.setdefault(key, value)


def _asyncpg_url(sqlalchemy_url: str) -> str:
    return re.sub(r"^postgresql\+asyncpg://", "postgresql://", sqlalchemy_url)


TABLES = [
    "peer_reviews",
    "highlights",
    "rating_events",
    "player_game_stats",
    "match_result_confirmations",
    "match_rosters",
    "media_sessions",
    "matches",
    "availability_slots",
    "courts",
    "facilities",
    "sport_profiles",
    "player_follows",
    "players",
    "users",
]


async def wipe(db_url: str) -> None:
    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg is not installed. Run: pip install asyncpg")
        sys.exit(1)

    conn = await asyncpg.connect(db_url)
    try:
        table_list = ", ".join(TABLES)
        await conn.execute(
            f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"
        )
        print(f"✓ Wiped {len(TABLES)} tables. Database is clean.")
    finally:
        await conn.close()


def main() -> None:
    _load_env()
    raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://sportout:sportout@localhost:5432/sportout",
    )
    db_url = _asyncpg_url(raw_url)
    print(f"Connecting to: {db_url}")
    print("This will permanently delete ALL rows from ALL tables.")
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)
    asyncio.run(wipe(db_url))


if __name__ == "__main__":
    main()
