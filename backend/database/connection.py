"""
Module   : DB Connection
Owner    : Database Engineer
Purpose  : PostgreSQL/SQLite connection/session setup with pgvector support.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.config import settings

_engine: AsyncEngine | None = None
_SessionFactory: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Get or create the async SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    url = database_url or settings.database_url

    # SQLite-specific connect args
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    _engine = create_async_engine(
        url,
        echo=settings.env == "development",
        poolclass=NullPool if url.startswith("sqlite") else None,
        connect_args=connect_args,
    )
    return _engine


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _SessionFactory
    if _SessionFactory is not None:
        return _SessionFactory

    eng = engine or get_engine()
    _SessionFactory = async_sessionmaker(
        eng,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return _SessionFactory


async def get_db(database_url: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session (async generator)."""
    factory = get_session_factory(get_engine(database_url))
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context(database_url: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    """Context manager version for non-FastAPI usage."""
    async for session in get_db(database_url):
        yield session
        break


async def init_db(database_url: str | None = None) -> None:
    """Initialize database tables and pgvector extension."""
    from backend.database.models import Base

    engine = get_engine(database_url)

    # Enable pgvector extension for PostgreSQL
    if database_url and database_url.startswith("postgresql"):
        async with engine.begin() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"[db] Initialized database at {database_url or settings.database_url}")


async def close_db() -> None:
    """Close database connections."""
    global _engine, _SessionFactory
    if _engine:
        await _engine.dispose()
        _engine = None
        _SessionFactory = None
