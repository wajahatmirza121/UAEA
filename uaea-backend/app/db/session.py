"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# SQLite (used in tests) uses NullPool and rejects pool_size/max_overflow
_engine_kwargs: dict = {"echo": False}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(pool_size=20, max_overflow=10)

engine = create_async_engine(settings.database_url, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
