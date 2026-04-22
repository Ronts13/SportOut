# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<project_context>
**Project:** SportOut
**Mission:** A hardcore street sports platform for competitive players.
**Current Phase:** Football MVP.
**Core Feature:** "AI Combine" — A player evaluation system mapped to 4 pillars (Pace, Shooting, Dribbling, Technique). 
**Methodology:** We currently use a "Wizard of Oz" approach. Users upload videos of specific drills, and admins manually score them via the backend. This manual scoring serves as ground-truth data for future Computer Vision (CV) training.
**Vibe:** Elite, authentic street sports. 
</project_context>

<critical_rules>
1. ASYNC FIRST: All I/O is async. ALWAYS use `async def` and `await` throughout the FastAPI/SQLAlchemy stack.
2. IMMUTABLE RATING EVENTS: `RatingEvent` is append-only to allow algorithm replay. NEVER execute UPDATE or DELETE on rows in this table.
3. SCHEMA SEPARATION: NEVER expose ORM models directly to the API responses. Always use Pydantic request/response shapes in `app/schemas/`.
</critical_rules>

<lessons_learned>
# 🛑 Known Mistakes to Avoid (Update this when Claude repeats an error)
- **Do not overwrite `elo_v1.py`:** When working on new rating features, create a new engine version (e.g., `elo_v2.py`). Leave `elo_v1.py` completely untouched.
- **Alembic Migrations:** Never generate a new migration without explicitly asking the user for confirmation first.
</lessons_learned>

## Commands

```bash
# Start the full stack (FastAPI app + PostgreSQL/PostGIS)
docker-compose up --build

# Run database migrations (required on first start)
docker-compose exec app alembic upgrade head

# Create a new migration after model changes
docker-compose exec app alembic revision --autogenerate -m "description"

# Validate schemas and engine wiring
python test_pulse.py

# API docs (Swagger UI)
open http://localhost:8000/docs
```

## Architecture

### Stack
FastAPI (async) + SQLAlchemy 2.0 (async) + PostgreSQL 16/PostGIS + Celery + Redis.

### Key Design Patterns

**Pluggable Rating Engines** (`app/engines/rating/`)
- `RatingEngine` ABC in `base.py` defines the interface: receives a `RatingContext`, returns a `RatingDelta`
- `EloRatingEngine` in `elo_v1.py` is the active implementation
- Registry in `__init__.py` — add new engines to `ENGINES` dict; switch via `RATING_ENGINE` env var

**Pluggable Filming Adapters** (`app/adapters/filming/`)
- `FilmingProvider` ABC in `base.py`: `start_session()`, `stop_session()`, `generate_highlights()`, `extract_video_metrics()`
- `ManualUploadAdapter` (default fallback) and `PixellotAdapter` (AI hardware) are concrete implementations
- Switch via `FILMING_PROVIDER` env var

**Multi-Sport Support** (`app/sports/`)
- `registry.py` maps `Sport` enum → stat schema
- `basketball.py` / `soccer.py` define per-sport `STAT_SCHEMAS`
- `PlayerGameStats.stats` is JSONB, validated at application layer against the sport's schema before insert

**Data Flow**
```text
Match ends → FilmingProvider.stop_session()
  → Celery: video.py worker generates highlights
  → Celery: ratings.py worker calls RatingEngine.compute()
  → RatingEvent row appended (immutable)
  → SportProfile.current_rating updated
```

### Layer Responsibilities
| Layer | Path | Purpose |
|---|---|---|
| Models | `app/models/` | SQLAlchemy ORM — source of truth for DB schema |
| Schemas | `app/schemas/` | Pydantic request/response shapes — never expose ORM models directly |
| Routers | `app/api/` | FastAPI route handlers — thin; delegate to engines/adapters |
| Engines | `app/engines/` | Pure business logic (no DB writes) |
| Adapters | `app/adapters/` | External provider integrations |
| Workers | `app/workers/` | Celery async tasks |

### Database
- PostGIS `POINT(SRID:4326)` for court/facility locations — use GeoAlchemy2 spatial types
- Async sessions via `app/core/database.py`; inject with `Depends(get_db)` from `app/api/dependencies.py`

### Environment Variables
Configured via pydantic-settings in `app/core/config.py`. Key vars:
- `DATABASE_URL` — `postgresql+asyncpg://...`
- `RATING_ENGINE` — engine key (e.g. `elo_v1`)
- `FILMING_PROVIDER` — adapter key (e.g. `manual_upload`, `pixellot`)
- `SECRET_KEY` — JWT signing

### Implementation State
Many endpoints raise `NotImplementedError` or return hardcoded mock data (e.g. `GET /players` leaderboard). The engine interfaces, adapters, models, and schemas are complete — endpoint implementations are the primary remaining work.