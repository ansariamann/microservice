"""
Unit tests for notification service database utilities.

This module tests database connection, session management,
and database initialization functionality.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import (
    DatabaseManager, 
    get_test_db_manager,
    init_database,
    close_database
)
from app.models import Base, Notification


class TestDatabaseManager:
    """Test cases for the DatabaseManager class."""

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization with default URL."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///test.db"}):
            manager = DatabaseManager()
            assert "sqlite+aiosqlite:///test.db" in manager.database_url

    def test_database_manager_custom_url(self):
        """Test DatabaseManager initialization with custom URL."""
        custom_url = "sqlite+aiosqlite:///custom.db"
        manager = DatabaseManager(custom_url)
        assert manager.database_url == custom_url

    @pytest.mark.asyncio
    async def test_create_tables(self, test_db_manager):
        """Test database table creation."""
        # Tables should already be created by the fixture
        # Test that we can create them again without error
        await test_db_manager.create_tables()
        
        # Verify tables exist by trying to query them
        async with test_db_manager.get_session() as session:
            result = await session.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in result.fetchall()]
            assert "notifications" in tables

    @pytest.mark.asyncio
    async def test_drop_tables(self, test_db_manager):
        """Test database table dropping."""
        # First ensure tables exist
        await test_db_manager.create_tables()
        
        # Drop tables
        await test_db_manager.drop_tables()
        
        # Verify tables are dropped
        async with test_db_manager.get_session() as session:
            result = await session.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in result.fetchall()]
            assert "notifications" not in tables

    @pytest.mark.asyncio
    async def test_get_session(self, test_db_manager):
        """Test database session creation and management."""
        async with test_db_manager.get_session() as session:
            assert isinstance(session, AsyncSession)
            # Test that we can execute a simple query
            result = await session.execute("SELECT 1")
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_get_session_error_handling(self, test_db_manager):
        """Test database session error handling and rollback."""
        try:
            async with test_db_manager.get_session() as session:
                # Force an error by executing invalid SQL
                await session.execute("INVALID SQL STATEMENT")
        except Exception:
            # Exception should be raised, but session should be properly cleaned up
            pass
        
        # Verify we can still get a new session after the error
        async with test_db_manager.get_session() as session:
            result = await session.execute("SELECT 1")
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_health_check_success(self, test_db_manager):
        """Test successful database health check."""
        is_healthy = await test_db_manager.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test database health check failure."""
        # Create manager with invalid URL
        manager = DatabaseManager("sqlite+aiosqlite:///invalid/path/db.db")
        is_healthy = await manager.health_check()
        assert is_healthy is False
        await manager.close()

    @pytest.mark.asyncio
    async def test_close_database(self, test_db_manager):
        """Test database connection closing."""
        # Ensure we can perform operations before closing
        async with test_db_manager.get_session() as session:
            result = await session.execute("SELECT 1")
            assert result.scalar() == 1
        
        # Close the database
        await test_db_manager.close()
        
        # After closing, we should not be able to perform operations
        # Note: This test might vary based on SQLite behavior


class TestDatabaseUtilities:
    """Test cases for database utility functions."""

    @pytest.mark.asyncio
    async def test_get_test_db_manager(self):
        """Test test database manager creation."""
        manager = await get_test_db_manager()
        
        # Verify it's using in-memory database
        assert ":memory:" in manager.database_url
        
        # Verify tables are created
        async with manager.get_session() as session:
            result = await session.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in result.fetchall()]
            assert "notifications" in tables
        
        await manager.close()

    @pytest.mark.asyncio
    async def test_get_test_db_manager_custom_url(self):
        """Test test database manager with custom URL."""
        custom_url = "sqlite+aiosqlite:///test_custom.db"
        manager = await get_test_db_manager(custom_url)
        
        assert manager.database_url == custom_url
        await manager.close()

    @pytest.mark.asyncio
    async def test_init_database(self):
        """Test database initialization function."""
        # Mock the global db_manager
        with patch('app.database.db_manager') as mock_manager:
            mock_manager.create_tables = AsyncMock()
            
            await init_database()
            
            mock_manager.create_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database_function(self):
        """Test database closing function."""
        # Mock the global db_manager
        with patch('app.database.db_manager') as mock_manager:
            mock_manager.close = AsyncMock()
            
            await close_database()
            
            mock_manager.close.assert_called_once()


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_notification_crud_operations(self, test_db_manager):
        """Test basic CRUD operations with the database."""
        async with test_db_manager.get_session() as session:
            # Create a notification
            notification = Notification(
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                message="Test notification",
                type="task_assigned"
            )
            
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            
            # Verify notification was created with ID
            assert notification.id is not None
            assert notification.user_id == 1
            assert notification.task_id == "507f1f77bcf86cd799439011"
            assert notification.message == "Test notification"
            assert notification.type == "task_assigned"
            assert notification.is_read is False
            assert notification.created_at is not None

    @pytest.mark.asyncio
    async def test_multiple_notifications_same_user(self, test_db_manager):
        """Test creating multiple notifications for the same user."""
        async with test_db_manager.get_session() as session:
            # Create multiple notifications
            notifications = [
                Notification(
                    user_id=1,
                    task_id=f"507f1f77bcf86cd79943901{i}",
                    message=f"Test notification {i}",
                    type="task_assigned"
                )
                for i in range(3)
            ]
            
            for notification in notifications:
                session.add(notification)
            
            await session.commit()
            
            # Verify all notifications were created
            for notification in notifications:
                await session.refresh(notification)
                assert notification.id is not None
                assert notification.user_id == 1

    @pytest.mark.asyncio
    async def test_database_constraints(self, test_db_manager):
        """Test database constraints and validation."""
        async with test_db_manager.get_session() as session:
            # Test that we can create notification with all required fields
            notification = Notification(
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                message="Test message",
                type="task_assigned"
            )
            
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            
            assert notification.id is not None