from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

print(f"DEBUG: Attempting to connect to Neon — URL prefix: {settings.DATABASE_URL[:40]}...", flush=True)
try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        connect_args={
            "timeout": 10,
            "statement_cache_size": 0,
            "server_settings": {"application_name": "sportout"},
        },
    )
    print("DEBUG: Engine created OK (no actual connection yet — happens on first query)", flush=True)
except Exception as _engine_err:
    print(f"DEBUG: Engine creation FAILED: {_engine_err}", flush=True)
    raise

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    print("DEBUG: get_db() called — opening DB session", flush=True)
    async with AsyncSessionFactory() as session:
        try:
            yield session
            print("DEBUG: get_db() committing", flush=True)
            await session.commit()
            print("DEBUG: get_db() committed OK", flush=True)
        except Exception as exc:
            print(f"DEBUG: get_db() rolling back due to: {exc}", flush=True)
            await session.rollback()
            raise
