import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _get_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(_get_url(), echo=False) if _get_url() else None

async_session = (
    async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    if engine
    else None
)


async def init_db() -> None:
    """Verify database connectivity at startup. Schema is managed by Alembic."""
    if engine is None:
        raise RuntimeError("DATABASE_URL is not set")
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)
