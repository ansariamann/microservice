"""
Test configuration and fixtures for Task Service tests.
"""

import asyncio
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

from app.database import DatabaseManager
from app.repository import TaskRepository
from app.models import TaskCreate, TaskStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create a test database connection."""
    # Use a test database
    test_db_url = "mongodb://localhost:27017/test_taskdb"
    client = AsyncIOMotorClient(test_db_url)
    database = client.test_taskdb
    
    # Clean up any existing test data
    await database.tasks.delete_many({})
    
    yield database
    
    # Clean up after tests
    await database.tasks.delete_many({})
    client.close()


@pytest_asyncio.fixture
async def task_repository(test_db):
    """Create a task repository instance with test database."""
    return TaskRepository(test_db)


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return TaskCreate(
        title="Test Task",
        description="This is a test task description",
        due_date=datetime.now() + timedelta(days=7),
        status=TaskStatus.TO_DO,
        assignee_id=2
    )


@pytest.fixture
def sample_task_data_no_assignee():
    """Sample task data without assignee for testing."""
    return TaskCreate(
        title="Unassigned Task",
        description="This task has no assignee",
        due_date=datetime.now() + timedelta(days=3),
        status=TaskStatus.TO_DO
    )


@pytest.fixture
def creator_id():
    """Sample creator ID for testing."""
    return 1


@pytest.fixture
def assignee_id():
    """Sample assignee ID for testing."""
    return 2