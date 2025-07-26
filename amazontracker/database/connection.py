"""
Database connection and session management
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..utils.config import settings, DatabaseConfig
from .models import Base

logger = logging.getLogger(__name__)

# Global database engine and session factory
engine = None
SessionLocal = None


def init_database():
    """Initialize database engine and session factory"""
    global engine, SessionLocal
    
    try:
        # Get engine configuration
        engine_config = DatabaseConfig.get_engine_config(settings.database_url)
        
        # Create engine
        if settings.database_url.startswith("sqlite"):
            # SQLite specific configuration
            engine = create_engine(
                settings.database_url,
                poolclass=StaticPool,
                **engine_config
            )
        else:
            # PostgreSQL and other databases
            engine = create_engine(
                settings.database_url,
                **engine_config
            )
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info(f"Database initialized: {settings.database_url}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        init_database()
    
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_session() as session:
            # Simple query to test connection
            session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        if engine is None:
            init_database()
        
        logger.warning("Resetting database - all data will be lost!")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database reset completed")
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise


# Initialize database on module import
if engine is None:
    init_database()
