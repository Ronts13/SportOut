import logging
import sys
import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import router as auth_router
from app.api.facilities import router as facilities_router
from app.api.matches import router as matches_router
from app.api.media import router as media_router
from app.api.players import router as players_router
from app.core.config import settings
from app.core.database import get_db

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
for _name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    logging.getLogger(_name).setLevel(logging.DEBUG)
logger = logging.getLogger("sportout")

# Print masked DB host so we can confirm .env is loaded
_db_host = settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "UNKNOWN (no @ in URL)"
print(f"SPORTOUT: main.py loaded — DB host: {_db_host}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    from app.core.database import engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registered after CORSMiddleware so it runs outermost — sees every request first
@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    print(f"DEBUG: Received {request.method} request to {request.url}", flush=True)
    response = await call_next(request)
    print(f"DEBUG: Responded with {response.status_code}", flush=True)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    tb_text = traceback.format_exc()
    sys.stderr.write("=" * 60 + "\n")
    sys.stderr.write(f"GLOBAL CRASH: {request.method} {request.url} — {exc}\n")
    sys.stderr.write(tb_text)
    sys.stderr.write("=" * 60 + "\n")
    sys.stderr.flush()
    return JSONResponse(status_code=500, content={"detail": f"{exc}\n\n{tb_text}"})

app.include_router(auth_router)
app.include_router(players_router, prefix="/api/v1")
app.include_router(matches_router, prefix="/api/v1")
app.include_router(facilities_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"ERROR: {exc}"
    return {"status": "ok", "version": settings.APP_VERSION, "db": db_status}
