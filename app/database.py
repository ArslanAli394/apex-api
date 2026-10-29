"""
Database connection and session management.
Provides SQLAlchemy setup and database utilities.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool, QueuePool
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create declarative base for ORM models
Base = declarative_base()

# Create database engine with connection pooling
if settings.is_testing:
    # Use NullPool for testing to avoid connection pool issues
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=settings.db_echo,
    )
else:
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=settings.db_pool_pre_ping,
        echo=settings.db_echo,
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """
    Dependency injection for database sessions.
    Used in FastAPI route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


async def check_db_connection() -> bool:
    """
    Check if database is accessible.
    Used for health checks.
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


def init_db():
    """
    Initialize database tables.
    Called on application startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def drop_db():
    """
    Drop all database tables.
    Used for testing cleanup.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {str(e)}")
        raise
