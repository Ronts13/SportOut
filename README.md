# SportOut

Community sports ecosystem — FastAPI backend + PostGIS + Neon Green UI.

---

## Quickstart (for Dan)

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 2. Clone the repo
```bash
git clone https://github.com/Ronts13/SportOut.git
cd SportOut
```

### 3. Create your local `.env` file
Copy the template below and save it as `.env` in the project root.  
**Never commit this file — it is git-ignored.**

```env
DATABASE_URL=postgresql+asyncpg://sportout:sportout@db:5432/sportout
RATING_ENGINE=elo_v1
FILMING_PROVIDER=manual_upload
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
SECRET_KEY=change-me-in-production
DEBUG=false
```

### 4. Start the stack
```bash
docker-compose up --build
```

- API docs: http://localhost:8000/docs
- Database: `localhost:5432` (user: `sportout`, password: `sportout`, db: `sportout`)

### 5. Run database migrations (first time only)
```bash
docker-compose exec app alembic upgrade head
```

---

## Project structure

```
app/
  api/        # FastAPI routers
  models/     # SQLAlchemy ORM models
  schemas/    # Pydantic request/response schemas
  engines/    # Pluggable rating engines (ELO, TrueSkill, …)
  adapters/   # Filming provider adapters (Pixellot, manual, …)
  core/       # Config, DB session, security helpers
  workers/    # Celery async tasks
alembic/      # DB migration scripts
frontend/     # UI (Neon Green theme)
```

---

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy DB URL — points to `db` service in Docker |
| `RATING_ENGINE` | Active rating engine ID (`elo_v1`, `trueskill_v1`, …) |
| `FILMING_PROVIDER` | Filming adapter (`manual_upload`, `pixellot`, …) |
| `SECRET_KEY` | JWT signing secret — **change before any deployment** |
| `DEBUG` | `true` enables hot-reload and verbose logging |
