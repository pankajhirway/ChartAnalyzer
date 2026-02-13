"""Database connection and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    Yields:
        AsyncSession: Database session for use in dependency injection.

    Example:
        ```python
        @app.get("/stocks/{symbol}")
        async def get_stock(symbol: str, db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            return result.scalar_one_or_none()
        ```
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database schema.

    Creates all tables if they don't exist. This should be called
    on application startup.
    """
    from app.models import Base  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections.

    This should be called on application shutdown.
    """
    await engine.dispose()
