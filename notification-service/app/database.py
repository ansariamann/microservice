"""
Database Connection and Session Management

This module provides database connection utilities, session management,
and database initialization for the notification service using PostgreSQL.
"""

import os
import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions for the notification service."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager with connection URL.
        
        Args:
            database_url: PostgreSQL database URL. Defaults to environment variable.
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://postgres:password@localhost:5432/taskmanagement"
        )
        
        # Configure synchronous engine for PostgreSQL
        self.engine = create_engine(
            self.database_url.replace("+asyncpg", ""),
            echo=os.getenv("DEBUG", "false").lower() == "true",
            pool_size=10,
            max_overflow=20
        )
        
        # Create session factory
        self.session = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False
        )
        
        logger.info(f"Database manager initialized with URL: {self.database_url}")

    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        try:
            with self.engine.begin() as conn:
                Base.metadata.create_all(conn)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def drop_tables(self) -> None:
        """Drop all database tables. Used for testing cleanup."""
        try:
            with self.engine.begin() as conn:
                Base.metadata.drop_all(conn)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Get a database session.
        
        Returns:
            Session: Database session for performing operations
        """
        return self.session()

    def close(self) -> None:
        """Close the database engine and all connections."""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
            raise

    def health_check(self) -> bool:
        """
        Perform a health check on the database connection.
        
        Returns:
            bool: True if database is accessible, False otherwise
        """
        session = None
        try:
            session = self.get_session()
            session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            if session:
                session.close()


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> Session:
    """
    Dependency function to get database session.
    
    Returns:
        Session: Database session
    """
    return db_manager.get_session()


def init_database() -> None:
    """Initialize the database by creating all tables."""
    db_manager.create_tables()


def close_database() -> None:
    """Close database connections on application shutdown."""
    db_manager.close()


# For testing purposes
def get_test_db_manager(test_db_url: str = "postgresql://postgres:password@localhost:5432/test_taskmanagement") -> DatabaseManager:
    """
    Create a test database manager with PostgreSQL test database.
    
    Args:
        test_db_url: Test database URL, defaults to PostgreSQL test database
        
    Returns:
        DatabaseManager: Test database manager instance
    """
    test_manager = DatabaseManager(test_db_url)
    test_manager.create_tables()
    return test_manager
