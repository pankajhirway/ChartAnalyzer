"""Database initialization script.

This script creates the database schema and can be run standalone
to initialize the database, or imported and called from main.py.
"""

import asyncio
import structlog

from app.config import get_settings
from app.database import init_db

logger = structlog.get_logger()


async def initialize_database() -> None:
    """Initialize the database schema.

    Creates all tables if they don't exist.
    """
    settings = get_settings()
    logger.info("Initializing database", database_url=settings.database_url)

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


def main() -> None:
    """Main entry point for standalone database initialization."""
    asyncio.run(initialize_database())


if __name__ == "__main__":
    main()
