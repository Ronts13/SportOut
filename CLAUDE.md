# SportOut — Claude Engineering Guide

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
**Source of truth for all Claude sessions on this project.**
Product decisions live in `PRODUCT_SPEC.md`. Business/marketing roadmap lives in `ROADMAP.md`.
This file covers architecture, current state, invariants, and what to build next.

---

<project_context>
**Project:** SportOut
**Mission:** To change amateur sports in the world by providing a hardcore street sports platform for competitive players.
**Current Phase:** Football (Soccer) MVP — this is the primary and only sport for v1 launch.
**Core Feature:** "AI Combine" — A player evaluation system mapped to 4 Football pillars (Pace, Shooting, Dribbling, Technique). Drills are fully designed in `MVP_DRILLS_PLAN.md`.
**Methodology:** We use a "Wizard of Oz" approach. Users upload drill videos; admins manually score them via the backend. Manual scores are direct ground-truth labels for future Computer Vision (CV) training.
**Vibe:** Elite, authentic street football.
**Long-term vision:** Global multi-sport social network. Padel, Tennis, Basketball are future expansions — their schemas exist in the codebase but are NOT the current focus.
</project_context>

<critical_rules>
1. ASYNC FIRST: All I/O is async. ALWAYS use `async def` and `await` throughout the FastAPI/SQLAlchemy stack.
2. IMMUTABLE RATING EVENTS: `RatingEvent` is append-only to allow algorithm replay. NEVER execute UPDATE or DELETE on rows in this table.
3. SCHEMA SEPARATION: NEVER expose ORM models directly to the API responses. Always use Pydantic request/response shapes in `app/schemas/`.
4. PLUGGABLE ENGINES: Call `get_active_engine()` — never instantiate `EloRatingEngine` directly. `RatingEngine.compute()` must be pure (no DB access, no side effects).
5. GEO FIRST: All locations use `Geometry("POINT", srid=4326)`. Proximity queries must use `ST_DWithin(...::geography, radius_meters)`. Never store lat/lon as plain floats.
6. ASYNC TASKS ONLY: Video processing, rating recalculation, notification dispatch → always Celery tasks. Never `await` long-running work inline in the API layer.
</critical_rules>

<lessons_learned>
# Known Mistakes to Avoid (Update this when Claude repeats an error)
- **Do not overwrite `elo_v1.py`:** When working on new rating features, create a new engine version (e.g., `elo_v2.py`). Leave `elo_v1.py` completely untouched.
- **Alembic Migrations:** Never generate a new migration without explicitly asking the user for confirmation first.
- **Raw dict across layers:** Never pass raw `dict` between service layers — all API boundaries use Pydantic models.
- **Geometry columns:** Do not store lat/lon as plain float columns; the `Geometry` type is canonical. Extract with `to_shape()` or `ST_X`/`ST_Y` in queries.
- **connect_args:** `statement_cache_size: 0` in `database.py` is intentional for PgBouncer/Neon compatibility. Do not remove it.
</lessons_learned>

---

## 1. Project in One Paragraph

The vision of SportOut is to change amateur sports in the world. We give every amateur athlete a **digital sports identity**: a credible rating, match history, highlight reel, and path to improvement — regardless of whether they play at a pro facility or a neighborhood court. The platform connects players to games at the right skill level, gives facility managers a live view of court activity, and gives scouts/coaches a structured talent pipeline.

**5 Pillars** *(validated as "Dream Features" in our latest user survey)*:
- Performance Stats & Dynamic Ratings *(Statistics & Performance)*
- Matchmaking *(Finding Partners & Players)*
- Smart Media *(Game Filming & Highlights)*
- Growth & Coaching *(Improvement Tools)*
- Municipal Information *(Information & Availability)*

---

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| API | FastAPI + Uvicorn | 0.110.3 / 0.30.6 |
| Runtime | Python | 3.12 |
| ORM | SQLAlchemy async | 2.0.36 |
| DB Driver | asyncpg | 0.29.0 |
| Migrations | Alembic | 1.13.3 |
| Database | PostgreSQL 16 + PostGIS 3.4 | Docker: `postgis/postgis:16-3.4` |
| Geospatial | GeoAlchemy2 | 0.15.2 |
| Validation | Pydantic v2 + pydantic-settings | 2.9.2 / 2.5.2 |
| Auth | PyJWT (HS256) + passlib/bcrypt | 2.9.0 / 1.7.4 |
| Task Queue | Celery + Redis | 5.4.0 / 5.1.1 |
| Frontend | Vanilla HTML/JS, Tailwind CDN, Leaflet | — |
| Container | Docker Compose | — |

**Production DB option:** Neon (serverless Postgres) — `.env.example` has the Neon URL template.

---

## 3. Repository Structure

```
app/
  main.py                   # FastAPI app factory, router registration, CORS
  core/
    config.py               # Settings (pydantic-settings, reads .env)
    database.py             # Async engine, AsyncSessionFactory, Base, get_db()
    enums.py                # All Enum classes (Sport, MatchStatus, UserRole, etc.)
    security.py             # hash_password, verify_password, create_access_token, decode_access_token
  models/                   # SQLAlchemy ORM — one file per domain entity
    user.py                 # User (auth record)
    player.py               # Player + PlayerFollow (social graph)
    sport_profile.py        # SportProfile (one per player per sport)
    facility.py             # Facility + Court + AvailabilitySlot
    match.py                # Match + MatchRoster + MatchResultConfirmation + PlayerGameStats
    rating.py               # RatingEvent (append-only log)
    peer_review.py          # PeerReview
    media.py                # MediaSession + Highlight
  schemas/                  # Pydantic request/response shapes — one file per domain
    player.py               # PlayerCreate, PlayerUpdate, PlayerProfileOut, LeaderboardEntryOut
    match.py                # MatchCreate, MatchOut, MatchResultSubmit, PlayerGameStatsCreate
    facility.py             # FacilityCreate, FacilityOut, CourtOut, CourtLiveUpdate
    rating.py               # RatingEventOut, RatingHistoryOut, PeerReviewCreate, PeerReviewOut
    media.py                # HighlightOut, MediaSessionOut, ManualUploadRequest
  engines/
    rating/
      base.py               # RatingEngine ABC, RatingContext, RatingDelta dataclasses
      elo_v1.py             # EloRatingEngine (format weights + peer review integration)
      __init__.py           # ENGINES registry + get_active_engine()
    matchmaking/
      base.py               # MatchmakingEngine ABC, MatchmakingQuery, MatchSuggestion (stub only)
  adapters/
    filming/
      base.py               # FilmingProvider ABC, HighlightRequest, HighlightResult
      manual_upload.py      # ManualUploadAdapter (fully working fallback)
      pixellot.py           # PixellotAdapter (stub — awaiting API access, OQ-02)
      __init__.py           # PROVIDERS registry + get_provider()
  api/                      # FastAPI routers — all use prefix /api/v1
    players.py              # /players — leaderboard & profile are MOCK; rest raise NotImplementedError
    matches.py              # /matches — ALL endpoints raise NotImplementedError
    facilities.py           # /facilities — nearby is MOCK; rest raise NotImplementedError
    media.py                # /media — ALL endpoints raise NotImplementedError
    dependencies.py         # get_current_user, get_current_facility_manager, get_current_admin
  sports/
    registry.py             # STAT_SCHEMAS dict + validate_game_stats()
    basketball.py           # BasketballGameStats (Pydantic, with computed rebounds_total)
    soccer.py               # SoccerGameStats (Pydantic, with shot consistency validation)
  workers/
    __init__.py             # celery_app factory
    ratings.py              # recalculate_match_ratings, replay_ratings_for_algorithm (stubs)
    video.py                # process_media_session, generate_player_highlight (stubs)
alembic/
  env.py                    # Async migration runner — imports all models explicitly
  versions/
    3f8a1c9b27e4_initial_schema.py   # All V1 tables (single migration)
frontend/
  index.html                # SPA: Home/Courts map, Rankings, LFG matches, Profile
  profile.html              # Player profile detail page
test_pulse.py               # Quick schema + engine smoke test (run with: python test_pulse.py)
```

---

## 4. Non-Negotiable Architecture Rules

These rules come from `PRODUCT_SPEC.md §6` and are baked into every design decision:

### 4.1 Events, Not Mutations
`rating_events` is an **append-only log**. Never UPDATE or DELETE rows from it.
- **Current rating** = latest `RatingEvent.rating_after` for `(player_id, sport)`.
- `SportProfile.current_rating` is a **denormalized cache** — updated by the rating worker after each game, never the source of truth.
- This enables full algorithm replay: change `RATING_ENGINE`, call `replay_ratings_for_algorithm`, and all history recalculates from the event log.

### 4.2 Pluggable Engines — Never Depend on a Concrete Implementation
Application code must call `get_active_engine()` from `app/engines/rating/__init__.py`, never instantiate `EloRatingEngine` directly.
Adding a new engine: implement `RatingEngine` ABC, add to `ENGINES` dict, no other changes needed.

The `RatingEngine.compute()` method must be **pure** — no DB access, no side effects. It takes a `RatingContext` and returns a `RatingDelta`. The worker assembles the context from DB; the engine knows nothing about the DB.

### 4.3 Pluggable Filming Provider
Call `get_provider(settings.FILMING_PROVIDER)`, never instantiate adapters directly.
Adding a new provider: implement `FilmingProvider` ABC, add to `PROVIDERS` dict.
`ManualUploadAdapter` is the always-working fallback — the platform must be fully functional without AI filming hardware.

### 4.4 Sport-Agnostic Core
`PlayerGameStats.stats` is a JSONB blob. The stat schema for each sport lives in `app/sports/`.
Adding a new sport = create `app/sports/newsport.py` with a Pydantic model + register in `STAT_SCHEMAS`. No DB migration needed.
Always validate stats with `validate_game_stats(sport, raw_dict)` before inserting into `player_game_stats`.

### 4.5 Async by Default for Heavy Work
Video processing, rating recalculation, notification dispatch → **always** Celery tasks.
The API layer must never `await` a long-running operation inline. Enqueue the task, return immediately.

### 4.6 Geo-Awareness is First-Class
All physical locations use `Geometry("POINT", srid=4326)` (WGS84).
Facility.location uses a GiST index (`ix_facilities_location`).
Proximity queries must use `ST_DWithin(location, ST_MakePoint(lon, lat)::geography, radius_meters)`.
Do NOT store lat/lon as plain floats in DB columns; the Geometry type is canonical.

### 4.7 Explicit Data Contracts
All API boundaries use Pydantic models. Never pass raw `dict` between service layers.
All FK constraints use `ondelete` policies — check the model before assuming behavior on delete.

---

## 5. Data Model — Key Relationships

```
User ──1:1── Player ──1:N── SportProfile        (one per sport played)
                   ──N:M── Match  (via MatchRoster)
                   ──1:N── RatingEvent            (append-only log)
                   ──N:M── PeerReview             (reviewer & reviewed)
                   ──1:N── Highlight              (direct FK for O(1) profile feed)
                   ──N:M── PlayerFollow            (self-referential social graph)

Facility ──1:N── Court ──1:N── AvailabilitySlot

Match ──N:1── Facility
      ──N:1── Court
      ──1:N── MatchRoster ──1:1── PlayerGameStats
      ──1:N── MatchResultConfirmation
      ──1:1── MediaSession ──1:N── Highlight
      ──1:N── RatingEvent
      ──1:N── PeerReview
```

**ID pattern:** `Player.id == User.id` — Player's PK is also a FK to `users.id`. A Player IS a User; no separate UUID.

**Circular FK resolution:** Models use `if TYPE_CHECKING:` imports for all cross-model relationships to avoid circular imports at runtime.

**Denormalized counters:** `Player.follower_count` / `Player.following_count` are denormalized — must be kept in sync when follow/unfollow actions occur in the service layer.

---

## 6. Current Implementation State

### Done — committed to git
- All SQLAlchemy ORM models (14 tables), Alembic initial migration
- `EloRatingEngine` (`elo_v1`) — pure, fully tested via `test_pulse.py`
- `RatingContext` / `RatingDelta` dataclasses + pure helpers (`determine_match_result`, `opponent_avg_rating`)
- `FilmingProvider` ABC + `ManualUploadAdapter` (working), `PixellotAdapter` (stub — OQ-02)
- `MatchmakingEngine` ABC + dataclasses (stub, no concrete implementation)
- All Pydantic schemas: player, match, facility, rating (incl. `CombineScoreCreate/Out`), media
- `SoccerGameStats` + `BasketballGameStats` validators, `STAT_SCHEMAS` registry
- JWT auth helpers + FastAPI auth dependencies
- Docker Compose (db + app — Redis/worker still missing)
- `test_pulse.py` smoke tests

### Done — uncommitted (staged for next commit)
- `POST /auth/token` — login endpoint, fully implemented (`app/api/auth.py`)
- `POST /api/v1/players/` — register (User + Player atomic transaction, duplicate guards)
- `GET /api/v1/players/leaderboard/{sport}` — real DB query on `sport_profiles`, city filter, rank
- `POST /api/v1/matches/` — create match + auto-roster the creator
- `GET /api/v1/matches/` — list open matches with optional PostGIS proximity + rating bracket filter
- `GET /api/v1/matches/{id}` — fetch single match
- `POST /api/v1/matches/{id}/join` — join with rating bracket enforcement
- `DELETE /api/v1/matches/{id}/leave` — leave (blocked if in-progress/completed)
- `POST /api/v1/matches/{id}/result` — submit home/away scores
- `POST /api/v1/matches/{id}/result/confirm` — 50% quorum logic → enqueues Celery task
- `recalculate_match_ratings` Celery task — **fully implemented** (loads match, builds RatingContext per player, appends RatingEvent rows, updates SportProfile cache)
- `Sport.PADEL` + `Sport.TENNIS` added to enum; `PadelGameStats`, `TennisGameStats` schemas registered
- `seed_db.py` + `wipe_db.py` utility scripts
- `CURRENT_STATE.md` snapshot (will be deleted — stale, replaced by this section)

### Not Implemented (raise `NotImplementedError` or missing)
- `POST /api/v1/matches/{id}/stats` — submit per-player game stats (Football: goals, assists, shots, position)
- `POST /api/v1/players/{id}/combine-score` — admin endpoint to manually score a player's AI Combine
- `GET /api/v1/players/{player_id}/rating/{sport}` — rating history time-series
- `GET /api/v1/players/{player_id}/highlights`
- `POST/DELETE /api/v1/players/{player_id}/follow` — follow/unfollow + counter sync
- `POST /api/v1/players/reviews` + `/reviews/{id}/confirm` — peer review flow
- `PATCH /api/v1/players/{player_id}` — profile update
- `GET /api/v1/facilities/{facility_id}` — needs geometry→lat/lon extraction
- `PATCH /api/v1/facilities/courts/{court_id}/live` — live court state
- **All** `/api/v1/media/*` endpoints
- Redis + Celery worker services in `docker-compose.yml`
- Frontend not yet wired to API (static mock arrays — needs `fetch()` calls)
- Football leaderboard mock data in frontend still shows Padel/Tennis players

---

## 7. Environment Setup

### Local (Docker)
```bash
cp .env.example .env           # fill SECRET_KEY at minimum
docker-compose up --build      # starts db (port 5432) + app (port 8000)
docker-compose exec app alembic upgrade head  # first time only
```
API docs: http://localhost:8000/docs
Health: http://localhost:8000/health

### Smoke test (no DB required)
```bash
python test_pulse.py
```

### Environment Variables
| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | asyncpg to localhost:5432 | Use Neon URL for prod: add `?ssl=require` |
| `RATING_ENGINE` | `elo_v1` | Must match a key in `ENGINES` registry |
| `FILMING_PROVIDER` | `manual_upload` | Must match a key in `PROVIDERS` registry |
| `SECRET_KEY` | `change-me-in-production` | **Change before any real deployment** |
| `DEBUG` | `false` | `true` enables uvicorn reload + SQLAlchemy echo |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | — |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | — |
| `S3_ENDPOINT_URL` | `None` | Set to MinIO URL for local dev; `None` = AWS S3 |

**Note on `database.py`:** `connect_args` includes `statement_cache_size: 0` — this is intentional for PgBouncer/Neon compatibility. Do not remove it.

---

## 8. Rating System Details

### Elo V1 (`app/engines/rating/elo_v1.py`)
- Base K-factor: `32.0`
- Format weights: LEAGUE_GAME=1.2, SCRIMMAGE=1.0, PICKUP=0.8, TRAINING=0.4
- Peer review contribution: `±0.15 * (avg_score - 3.0)` (neutral at 3/5)
- New player default rating: `1000.0` (in `SportProfile.current_rating`)
- Rating never goes below 0.0

**Rating scale decision pending (OQ-01):** ROADMAP specifies a 55–99 display scale with badge tiers. The internal Elo scale (1000-based) and the display scale are separate concerns — the display transformation is not yet implemented.

### Adding a New Rating Engine
1. Create `app/engines/rating/your_engine.py` implementing `RatingEngine` ABC
2. Add `"your_engine_id": YourEngineClass` to `ENGINES` in `app/engines/rating/__init__.py`
3. Set `RATING_ENGINE=your_engine_id` in `.env`
4. Run `replay_ratings_for_algorithm` task to backfill history

---

## 9. Sport Registry

### Adding a New Sport
1. Create `app/sports/newsport.py` with a Pydantic model extending `BaseModel`
2. Add positions `Enum` and `GameStats` model with field validators
3. Register in `app/sports/registry.py`: `STAT_SCHEMAS[Sport.NEW_SPORT] = NewSportGameStats`
4. Add the sport value to `Sport` enum in `app/core/enums.py`
5. No DB migration needed — stats are stored as JSONB

**Currently registered:** `Sport.SOCCER` → `SoccerGameStats` (**MVP primary**), `Sport.BASKETBALL` → `BasketballGameStats`, `Sport.PADEL` → `PadelGameStats`, `Sport.TENNIS` → `TennisGameStats`
**MVP focus:** Football (`Sport.SOCCER`) is the only active sport for v1. The others are registered for future expansion but have no active UI or leaderboard.
**`SoccerGameStats` fields:** `position_played` (gk/cb/fb/cm/wg/st), `minutes_played`, `goals`, `assists`, `shots_total`, `shots_on_target`, `pass_accuracy_pct`, `distance_covered_km`, `yellow_cards`, `red_cards`. Validator: `shots_on_target ≤ shots_total`.

---

## 10. API Patterns

### Adding a New Endpoint
1. Write the Pydantic schemas first in `app/schemas/`
2. Write the SQLAlchemy query in the router function or extract to a service function
3. Use `db: AsyncSession = Depends(get_db)` for DB access
4. Use `current_user: TokenData = Depends(get_current_user)` for auth
5. All DB queries must be `async` — use `await db.execute(select(...))` patterns
6. Never block the event loop with CPU-heavy work — offload to Celery

### Service Layer Pattern (when to extract)
If a router function needs to: run multiple queries, enqueue a task, update denormalized counters, or be reused by multiple endpoints → extract to a service function. No formal `services/` directory yet; these can live in the router file until there are 3+ endpoints sharing logic.

### FacilityOut Lat/Lon Serialization
`FacilityOut` has `latitude: float` / `longitude: float` fields but the DB stores `Geometry("POINT")`. When implementing the real `GET /facilities/{id}` endpoint, extract coordinates from the geometry using:
```python
from geoalchemy2.shape import to_shape
point = to_shape(facility.location)
latitude, longitude = point.y, point.x
```
Or use a SQLAlchemy `ST_X` / `ST_Y` expression in the query.

---

## 11. Frontend

**Stack:** Vanilla HTML + Tailwind CSS (CDN) + Leaflet.js (maps). Single-page app with JS tab switching.

**Design language:**
- Background: pure black (`#000000` / `#0a0a0a`)
- Accent: Neon Green `#39FF14` (teal-glow) with glow shadows
- Font: Inter
- Dark mode only (`class="dark"` on `<html>`)

**Two files:**
- `frontend/index.html` — main SPA (Home, Courts map, Rankings/Leaderboard, LFG matches)
- `frontend/profile.html` — player profile detail

**Current state:** UI is static/mock. API calls to backend are not yet wired up.

**Sports shown in frontend:** Currently displays mock Padel/Tennis leaderboard data — **must be updated to Football before any demo**. The mock array in `app/api/players.py` and the hardcoded JS in `frontend/index.html` both need to reflect Football players.

**Football frontend priorities:** Leaderboard filtered to `sport=soccer`, match creation form with Football positions (gk/cb/fb/cm/wg/st), post-match stat entry form aligned to `SoccerGameStats`.

---

## 12. Auth — Current State & What's Missing

**Implemented:**
- `hash_password()` / `verify_password()` (bcrypt)
- `create_access_token()` / `decode_access_token()` (JWT HS256)
- FastAPI dependencies: `get_current_user`, `get_current_facility_manager`, `get_current_admin`

**Implemented (uncommitted):**
- `POST /auth/token` — done in `app/api/auth.py`, registered in `app/main.py`
- `POST /api/v1/players/` — player registration done (User + Player + SportProfile)

**Still missing:**
- Refresh token endpoint
- Social login (Google/Instagram/Facebook) — ROADMAP item, architecture not yet decided

---

## 13. Celery Workers

### Running Workers Locally
```bash
# In a separate terminal (Redis must be running)
celery -A app.workers worker --loglevel=info
```
Docker Compose does not yet include a `worker` service — add one when needed.

### Task Contracts

**`recalculate_match_ratings(match_id: str)`** — **FULLY IMPLEMENTED** (uncommitted). Triggered after 50% quorum on result confirmation:
1. Idempotency guard: skips if `RatingEvent` rows already exist for this match
2. Loads Match + MatchRosters + per-roster `game_stats`
3. Loads `SportProfile` (current ratings) for all attending players
4. Loads `PeerReview` rows for this match; aggregates per-player mean score
5. For each attending player: builds `RatingContext` → calls `get_active_engine().compute()` (pure)
6. Appends `RatingEvent` rows (APPEND ONLY — never UPDATE/DELETE)
7. Updates denormalized `SportProfile.current_rating` + `career_games` + `career_wins`

**`process_media_session(media_session_id: str)`** — stub. Not needed for Football MVP without Pixellot access.

**`replay_ratings_for_algorithm(sport, new_version)`** — stub. Used only when switching algorithm versions.

---

## 14. Open Questions (Unresolved)

From `PRODUCT_SPEC.md §7` — do not make architectural decisions that close these without discussion:

| ID | Question | Impact | Status |
|---|---|---|---|
| OQ-01 | Final rating algorithm (Elo is placeholder) | Low — architecture is algorithm-agnostic | Open — Elo v1 ships for MVP |
| OQ-02 | Pixellot API access | Medium — `PixellotAdapter` is a stub; `ManualUploadAdapter` is the fallback | Open — not blocking Football MVP |
| OQ-04 | Sports in scope for v1 | **CLOSED** — Football (Soccer) is the v1 MVP sport | Closed |
| OQ-06 | Video consent model (especially minors) | High — legal review required before video features ship | Open — not blocking text-stat MVP |
| Rating scale | Internal Elo (1000-base) vs. 55–99 display scale | Medium — display transform not yet implemented | Open — implement in leaderboard API |
| Sports mismatch | Frontend shows Padel/Tennis; backend has all 4 sports | **CLOSED** — Football is primary; frontend to be updated | Closed |
| AI Combine flow | Admin scoring endpoint not yet wired to Elo delta | High — needed to connect `CombineScoreCreate` to a `RatingEvent` | Open — next Football sprint |

---

## 15. Next Sprint Priorities — Football MVP (in order)

**Prerequisite: commit the current uncommitted work first.**

1. **`POST /api/v1/matches/{id}/stats`** — Submit per-player Football game stats (`SoccerGameStats`: goals, assists, shots, position, minutes). Validates via `validate_game_stats(Sport.SOCCER, raw)`. This is the last missing piece of the core match loop.

2. **`POST /api/v1/players/{id}/combine-score` (admin)** — Admin manually enters AI Combine pillar scores (Pace 0–100, Shooting, Dribbling, Technique). Endpoint computes a weighted combine score, appends a `RatingEvent` with `source_type=VIDEO_ANALYSIS`, and updates `SportProfile.current_rating`. Schemas `CombineScoreCreate` / `CombineScoreOut` are already defined in `app/schemas/rating.py`.

3. **Redis + Celery worker in `docker-compose.yml`** — Add `redis` service and a `worker` service (`celery -A app.workers worker`). Without this, `recalculate_match_ratings` is enqueued but never executed.

4. **Football leaderboard mock data** — Update mock array in `app/api/players.py` to use Football players (`sport="soccer"`). Update frontend JS to default to `sport=soccer`.

5. **`GET /api/v1/players/{player_id}/rating/{sport}`** — Rating history time-series from `rating_events`. Drives the profile rating trend chart.

6. **Peer review endpoints** — `POST /api/v1/players/reviews` + `/reviews/{id}/confirm`. Feeds into Elo via `peer_review_score` in `RatingContext`.

7. **Frontend `fetch()` wiring** — Replace hardcoded JS arrays with real API calls: `/players/leaderboard/soccer`, `/matches/`, `/facilities/nearby`. This is the last step before the platform is demoed end-to-end.

---

## 16. Code Style Rules

- Python 3.12 — use `str | None` union syntax, not `Optional[str]`
- All model relationships use `Mapped[...]` typed annotations (SQLAlchemy 2.0 style)
- `from __future__ import annotations` at top of all model files (enables forward references)
- Pydantic models use `model_config = ConfigDict(from_attributes=True)` for ORM serialization
- Enums are `str, Enum` subclasses so their values serialize naturally to JSON
- No inline comments explaining WHAT code does; only WHY when non-obvious
- No docstrings on simple functions; docstrings only on public interfaces (ABCs, complex workers)
- DB session management: use `get_db()` dependency — it auto-commits on success, rollbacks on exception
- All geo queries use `ST_DWithin` with `::geography` cast for accurate meter-based distance
