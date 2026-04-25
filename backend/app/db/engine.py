from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings

_engine = (
    create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=False,
        future=True,
    )
    if settings.database_url
    else None
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = (
    async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    if _engine is not None
    else None
)


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """FastAPI dependency — yields an AsyncSession or None when no DB is configured."""
    if AsyncSessionLocal is None:
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
