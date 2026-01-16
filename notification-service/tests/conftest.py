"""
Test configuration and fixtures for notification service tests.

This module provides pytest fixtures for database testing,
including test database setup and cleanup.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_test_db_manager, DatabaseManager
from app.repository import NotificationRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """
    Create a test database manager with in-memory SQLite.
    
    Yields:
        DatabaseManager: Test database manager instance
    """
    manager = await get_test_db_manager()
    yield manager
    await manager.close()


@pytest.fixture
async def db_session(test_db_manager: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Args:
        test_db_manager: Test database manager fixture
        
    Yields:
        AsyncSession: Test database session
    """
    async with test_db_manager.get_session() as session:
        yield session


@pytest.fixture
async def notification_repository(db_session: AsyncSession) -> AsyncGenerator[NotificationRepository, None]:
    """
    Create a notification repository for testing.
    
    Args:
        db_session: Test database session fixture
        
    Yields:
        NotificationRepository: Repository instance for testing
    """
    repo = NotificationRepository(db_session)
    yield repo


@pytest.fixture
def sample_notification_data():
    """
    Provide sample notification data for testing.
    
    Returns:
        dict: Sample notification data
    """
    return {
        "user_id": 1,
        "task_id": "507f1f77bcf86cd799439011",
        "message": "You have been assigned to task 'Test Task' by John Doe",
        "type": "task_assigned"
    }


@pytest.fixture
def multiple_notification_data():
    """
    Provide multiple notification records for testing.
    
    Returns:
        list: List of notification data dictionaries
    """
    return [
        {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "You have been assigned to task 'Task 1' by John Doe",
            "type": "task_assigned"
        },
        {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439012",
            "message": "Task 'Task 2' status has been updated to 'in_progress'",
            "type": "task_updated"
        },
        {
            "user_id": 2,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "You have been assigned to task 'Task 1' by Jane Smith",
            "type": "task_assigned"
        }
    ]