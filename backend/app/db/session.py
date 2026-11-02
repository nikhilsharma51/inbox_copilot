"""
Database session management using SQLAlchemy 2.0 async.

Provides async engine, session factory, and connection utilities.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

engine = None
SessionLocal = None


async def init_db() -> None:
    global engine, SessionLocal

    logger.info("database.init", url=settings.database_url)

    engine = create_async_engine(
        settings.database_url,
        echo=(settings.environment == "dev"),  # Log SQL in dev
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  
        pool_recycle=3600,  
    )

  
    SessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    logger.info("database.initialized")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
 
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() at startup.")

    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    global engine

    if engine is not None:
        logger.info("database.close")
        await engine.dispose()
        engine = None
